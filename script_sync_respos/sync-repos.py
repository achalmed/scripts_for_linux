#!/usr/bin/env python3
"""
Script de sincronización de múltiples repositorios Git
Autor: Edison Achalma
Descripción: Automatiza el proceso de add, commit y push en múltiples repos
"""

import os
import sys
import subprocess
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Colores ANSI
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

@dataclass
class RepoStatus:
    name: str
    success: bool
    has_changes: bool
    message: str

class GitRepoSync:
    def __init__(self, config_file: str = "repos-config.yml"):
        self.config = self.load_config(config_file)
        self.results: List[RepoStatus] = []
        
    def load_config(self, config_file: str) -> Dict:
        """Cargar configuración desde archivo YAML"""
        config_path = Path(config_file)
        if not config_path.exists():
            self.print_error(f"Archivo de configuración no encontrado: {config_file}")
            return self.get_default_config()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_default_config(self) -> Dict:
        """Configuración por defecto si no existe archivo"""
        return {
            'base_directory': str(Path.home() / 'Projects'),
            'repositories': [],
            'commit_messages': {
                'default': 'update: sincronización automática de contenidos'
            },
            'settings': {
                'auto_pull': True,
                'check_branch': True,
                'verbose': False,
                'parallel': False,
                'max_retries': 3
            }
        }
    
    @staticmethod
    def print_info(msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
    
    @staticmethod
    def print_success(msg: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")
    
    @staticmethod
    def print_warning(msg: str):
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")
    
    @staticmethod
    def print_error(msg: str):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")
    
    def run_git_command(self, repo_path: Path, command: List[str], 
                       verbose: bool = False) -> Tuple[bool, str]:
        """Ejecutar comando git y retornar resultado"""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if verbose and result.stdout:
                print(result.stdout)
            
            if result.returncode != 0:
                return False, result.stderr
            
            return True, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Comando excedió el tiempo límite"
        except Exception as e:
            return False, str(e)
    
    def detect_commit_type(self, repo_path: Path) -> str:
        """Auto-detectar tipo de commit basado en archivos cambiados"""
        success, output = self.run_git_command(repo_path, ['diff', '--name-only', 'HEAD'])
        
        if not success:
            return 'default'
        
        changed_files = output.strip().split('\n')
        patterns = self.config.get('auto_detect_patterns', {})
        
        # Verificar patrones en orden de prioridad
        for commit_type, file_patterns in patterns.items():
            for pattern in file_patterns:
                for file in changed_files:
                    if self._match_pattern(file, pattern):
                        return commit_type
        
        return 'default'
    
    @staticmethod
    def _match_pattern(filename: str, pattern: str) -> bool:
        """Verificar si un archivo coincide con un patrón"""
        pattern = pattern.replace('**/', '.*/')
        pattern = pattern.replace('*', '.*')
        return bool(re.match(pattern, filename))
    
    def check_repo_status(self, repo_path: Path) -> bool:
        """Verificar si hay cambios en el repositorio"""
        success, _ = self.run_git_command(repo_path, ['diff-index', '--quiet', 'HEAD', '--'])
        return not success  # Retorna True si hay cambios
    
    def sync_repository(self, repo: Dict, commit_msg: str = None, 
                       check_only: bool = False, verbose: bool = False) -> RepoStatus:
        """Sincronizar un repositorio individual"""
        repo_name = repo['name']
        base_dir = Path(self.config['base_directory']).expanduser()
        repo_path = base_dir / repo_name
        
        print(f"\n{'='*60}")
        self.print_info(f"Procesando: {Colors.YELLOW}{repo_name}{Colors.NC}")
        print('='*60)
        
        # Verificar si existe el directorio
        if not repo_path.exists():
            self.print_error(f"Directorio no encontrado: {repo_path}")
            return RepoStatus(repo_name, False, False, "Directorio no encontrado")
        
        # Verificar si es un repositorio git
        if not (repo_path / '.git').exists():
            self.print_error(f"No es un repositorio Git: {repo_path}")
            return RepoStatus(repo_name, False, False, "No es repositorio Git")
        
        # Verificar rama actual
        if self.config['settings'].get('check_branch', True):
            success, current_branch = self.run_git_command(repo_path, ['branch', '--show-current'])
            if success:
                current_branch = current_branch.strip()
                expected_branch = repo.get('branch', 'main')
                if current_branch != expected_branch:
                    self.print_warning(f"Rama actual: {current_branch}, esperada: {expected_branch}")
        
        # Auto pull si está configurado
        if self.config['settings'].get('auto_pull', True) and not check_only:
            self.print_info("Actualizando desde remoto...")
            success, output = self.run_git_command(repo_path, ['pull'], verbose)
            if not success:
                self.print_warning(f"Error en pull: {output}")
        
        # Verificar cambios
        has_changes = self.check_repo_status(repo_path)
        
        if not has_changes:
            self.print_warning(f"No hay cambios en {repo_name}")
            return RepoStatus(repo_name, True, False, "Sin cambios")
        
        self.print_info(f"Cambios detectados en {repo_name}")
        
        # Mostrar cambios si verbose
        if verbose:
            self.run_git_command(repo_path, ['status', '--short'], verbose=True)
        
        # Si es solo verificación, salir
        if check_only:
            success, files = self.run_git_command(repo_path, ['status', '--short'])
            print(files)
            return RepoStatus(repo_name, True, True, "Cambios detectados (solo verificación)")
        
        # Determinar mensaje de commit
        if commit_msg is None:
            commit_type = self.detect_commit_type(repo_path)
            commit_msg = self.config['commit_messages'].get(
                commit_type, 
                self.config['commit_messages']['default']
            )
            self.print_info(f"Tipo de commit detectado: {commit_type}")
        
        # Git add
        self.print_info("Agregando cambios...")
        success, output = self.run_git_command(repo_path, ['add', '-A'], verbose)
        if not success:
            self.print_error(f"Error en git add: {output}")
            return RepoStatus(repo_name, False, True, f"Error en add: {output}")
        
        # Git commit
        self.print_info(f"Creando commit: '{commit_msg}'")
        success, output = self.run_git_command(repo_path, ['commit', '-m', commit_msg], verbose)
        if not success:
            self.print_error(f"Error en git commit: {output}")
            return RepoStatus(repo_name, False, True, f"Error en commit: {output}")
        
        # Git push
        self.print_info("Enviando cambios al repositorio remoto...")
        max_retries = self.config['settings'].get('max_retries', 3)
        
        for attempt in range(max_retries):
            success, output = self.run_git_command(repo_path, ['push'], verbose)
            if success:
                self.print_success(f"✓ {repo_name} sincronizado exitosamente")
                return RepoStatus(repo_name, True, True, "Sincronizado exitosamente")
            
            if attempt < max_retries - 1:
                self.print_warning(f"Reintentando... ({attempt + 1}/{max_retries})")
        
        self.print_error(f"Error en git push después de {max_retries} intentos: {output}")
        return RepoStatus(repo_name, False, True, f"Error en push: {output}")
    
    def sync_all(self, repo_names: List[str] = None, commit_msg: str = None,
                check_only: bool = False, verbose: bool = False):
        """Sincronizar todos los repositorios o solo los especificados"""
        
        # Filtrar repositorios
        repos = self.config.get('repositories', [])
        if repo_names:
            repos = [r for r in repos if r['name'] in repo_names]
        
        repos = [r for r in repos if r.get('enabled', True)]
        
        if not repos:
            self.print_error("No hay repositorios para sincronizar")
            return
        
        # Imprimir encabezado
        print("\n" + "╔" + "═"*60 + "╗")
        print("║" + " "*10 + "SINCRONIZACIÓN DE REPOSITORIOS GIT" + " "*16 + "║")
        print("╚" + "═"*60 + "╝\n")
        
        self.print_info(f"Repositorios a procesar: {len(repos)}")
        if check_only:
            self.print_warning("Modo verificación (no se harán commits ni push)")
        
        # Procesar repositorios
        if self.config['settings'].get('parallel', False) and not check_only:
            self._sync_parallel(repos, commit_msg, verbose)
        else:
            self._sync_sequential(repos, commit_msg, check_only, verbose)
        
        # Imprimir resumen
        self._print_summary()
    
    def _sync_sequential(self, repos: List[Dict], commit_msg: str,
                        check_only: bool, verbose: bool):
        """Sincronizar repositorios secuencialmente"""
        for repo in repos:
            result = self.sync_repository(repo, commit_msg, check_only, verbose)
            self.results.append(result)
    
    def _sync_parallel(self, repos: List[Dict], commit_msg: str, verbose: bool):
        """Sincronizar repositorios en paralelo"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.sync_repository, repo, commit_msg, False, verbose): repo
                for repo in repos
            }
            
            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
    
    def _print_summary(self):
        """Imprimir resumen de la sincronización"""
        success_count = sum(1 for r in self.results if r.success and r.has_changes)
        no_changes_count = sum(1 for r in self.results if r.success and not r.has_changes)
        error_count = sum(1 for r in self.results if not r.success)
        
        print("\n" + "="*60)
        print(" "*20 + "RESUMEN DE SINCRONIZACIÓN")
        print("="*60)
        self.print_success(f"Exitosos: {success_count}")
        self.print_warning(f"Sin cambios: {no_changes_count}")
        self.print_error(f"Errores: {error_count}")
        print("="*60 + "\n")
        
        # Mostrar detalles de errores
        errors = [r for r in self.results if not r.success]
        if errors:
            print("\nDetalles de errores:")
            for result in errors:
                self.print_error(f"  - {result.name}: {result.message}")

def main():
    parser = argparse.ArgumentParser(
        description='Sincronizar múltiples repositorios Git',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                                    # Sincronizar todos los repos
  %(prog)s -m "feat: nueva funcionalidad"    # Con mensaje personalizado
  %(prog)s -r axiomata chaska                # Solo repos específicos
  %(prog)s -c                                # Solo verificar cambios
  %(prog)s -v                                # Modo verbose
  %(prog)s --config mi-config.yml            # Usar archivo de config personalizado
        """
    )
    
    parser.add_argument('-m', '--message', 
                       help='Mensaje personalizado para el commit')
    parser.add_argument('-r', '--repos', nargs='+',
                       help='Repositorios específicos a sincronizar')
    parser.add_argument('-c', '--check', action='store_true',
                       help='Solo verificar cambios sin hacer commit/push')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Modo verbose (más detalles)')
    parser.add_argument('--config', default='repos-config.yml',
                       help='Archivo de configuración (default: repos-config.yml)')
    parser.add_argument('--parallel', action='store_true',
                       help='Procesar repositorios en paralelo')
    
    args = parser.parse_args()
    
    try:
        syncer = GitRepoSync(args.config)
        
        # Override config con argumentos de línea de comandos
        if args.parallel:
            syncer.config['settings']['parallel'] = True
        if args.verbose:
            syncer.config['settings']['verbose'] = True
        
        syncer.sync_all(
            repo_names=args.repos,
            commit_msg=args.message,
            check_only=args.check,
            verbose=args.verbose
        )
        
        # Exit code basado en resultados
        if any(not r.success for r in syncer.results):
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Error inesperado:{Colors.NC} {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
