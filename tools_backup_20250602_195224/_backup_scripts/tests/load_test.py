#!/usr/bin/env python3
# Script para realizar pruebas de carga en la aplicación
# Creado: 18/05/2025

import os
import sys
import time
import json
import datetime
import argparse
import threading
import requests
import statistics
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

# Configuración
DEFAULT_BASE_URL = "http://127.0.0.1:8002"
DEFAULT_CONCURRENCY = 10
DEFAULT_REQUESTS = 100
DEFAULT_TIMEOUT = 10
RESULTS_DIR = "/logs/load_tests"

# Asegurarse de que el directorio de resultados existe
os.makedirs(RESULTS_DIR, exist_ok=True)

class LoadTest:
    def __init__(self, base_url, endpoints, concurrency, num_requests, timeout):
        self.base_url = base_url
        self.endpoints = endpoints
        self.concurrency = concurrency
        self.num_requests = num_requests
        self.timeout = timeout
        self.results = {}
        
        # Inicializar resultados para cada endpoint
        for endpoint in endpoints:
            self.results[endpoint] = {
                "response_times": [],
                "status_codes": [],
                "errors": []
            }
    
    def make_request(self, endpoint):
        """Realiza una solicitud HTTP a un endpoint específico"""
        url = urljoin(self.base_url, endpoint)
        start_time = time.time()
        try:
            response = requests.get(url, timeout=self.timeout)
            elapsed_time = time.time() - start_time
            
            return {
                "url": url,
                "status_code": response.status_code,
                "response_time": elapsed_time,
                "success": 200 <= response.status_code < 300,
                "error": None
            }
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            return {
                "url": url,
                "status_code": None,
                "response_time": elapsed_time,
                "success": False,
                "error": str(e)
            }
    
    def worker(self, endpoint):
        """Función de trabajo para cada hilo"""
        results = []
        for _ in range(self.num_requests // self.concurrency):
            result = self.make_request(endpoint)
            results.append(result)
        return results
    
    def run_test(self):
        """Ejecuta la prueba de carga"""
        print(f"Iniciando prueba de carga con {self.concurrency} hilos concurrentes")
        print(f"Realizando {self.num_requests} solicitudes a {len(self.endpoints)} endpoints")
        
        start_time = time.time()
        
        for endpoint in self.endpoints:
            print(f"Probando endpoint: {endpoint}")
            
            # Crear un grupo de hilos
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                # Enviar las solicitudes
                futures = [executor.submit(self.worker, endpoint) for _ in range(self.concurrency)]
                
                # Recopilar resultados
                for future in futures:
                    results = future.result()
                    for result in results:
                        if result["success"]:
                            self.results[endpoint]["response_times"].append(result["response_time"])
                            self.results[endpoint]["status_codes"].append(result["status_code"])
                        else:
                            self.results[endpoint]["errors"].append(result["error"])
        
        total_time = time.time() - start_time
        
        # Calcular estadísticas
        self.calculate_statistics(total_time)
    
    def calculate_statistics(self, total_time):
        """Calcula estadísticas para los resultados de la prueba"""
        self.statistics = {
            "total_time": total_time,
            "total_requests": self.num_requests * len(self.endpoints),
            "requests_per_second": (self.num_requests * len(self.endpoints)) / total_time,
            "endpoints": {}
        }
        
        for endpoint, data in self.results.items():
            response_times = data["response_times"]
            status_codes = data["status_codes"]
            errors = data["errors"]
            
            if response_times:
                stats = {
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "avg_response_time": statistics.mean(response_times),
                    "median_response_time": statistics.median(response_times),
                    "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                    "success_rate": len(response_times) / self.num_requests * 100,
                    "error_rate": len(errors) / self.num_requests * 100,
                    "status_code_distribution": {}
                }
                
                # Calcular distribución de códigos de estado
                for code in set(status_codes):
                    stats["status_code_distribution"][code] = status_codes.count(code)
            else:
                stats = {
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "avg_response_time": 0,
                    "median_response_time": 0,
                    "p95_response_time": 0,
                    "success_rate": 0,
                    "error_rate": 100,
                    "status_code_distribution": {}
                }
            
            self.statistics["endpoints"][endpoint] = stats
    
    def print_results(self):
        """Imprime los resultados de la prueba"""
        print("\n" + "="*80)
        print("RESULTADOS DE LA PRUEBA DE CARGA")
        print("="*80)
        
        print(f"Tiempo total: {self.statistics['total_time']:.2f} segundos")
        print(f"Solicitudes totales: {self.statistics['total_requests']}")
        print(f"Solicitudes por segundo: {self.statistics['requests_per_second']:.2f}")
        
        for endpoint, stats in self.statistics["endpoints"].items():
            print("\n" + "-"*80)
            print(f"Endpoint: {endpoint}")
            print(f"Tasa de éxito: {stats['success_rate']:.2f}%")
            print(f"Tasa de error: {stats['error_rate']:.2f}%")
            print(f"Tiempo de respuesta mínimo: {stats['min_response_time']*1000:.2f} ms")
            print(f"Tiempo de respuesta máximo: {stats['max_response_time']*1000:.2f} ms")
            print(f"Tiempo de respuesta promedio: {stats['avg_response_time']*1000:.2f} ms")
            print(f"Tiempo de respuesta mediano: {stats['median_response_time']*1000:.2f} ms")
            print(f"Tiempo de respuesta P95: {stats['p95_response_time']*1000:.2f} ms")
            
            print("Distribución de códigos de estado:")
            for code, count in stats["status_code_distribution"].items():
                print(f"  {code}: {count} ({count/self.num_requests*100:.2f}%)")
            
            if self.results[endpoint]["errors"]:
                print(f"Errores ({len(self.results[endpoint]['errors'])}):")
                for error in self.results[endpoint]["errors"][:5]:
                    print(f"  {error}")
                if len(self.results[endpoint]["errors"]) > 5:
                    print(f"  ... y {len(self.results[endpoint]['errors']) - 5} más")
    
    def generate_charts(self, output_dir):
        """Genera gráficos para visualizar los resultados"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        charts_dir = os.path.join(output_dir, f"load_test_{timestamp}")
        os.makedirs(charts_dir, exist_ok=True)
        
        # Gráfico de tiempos de respuesta por endpoint
        plt.figure(figsize=(12, 6))
        endpoints = list(self.statistics["endpoints"].keys())
        avg_times = [self.statistics["endpoints"][ep]["avg_response_time"]*1000 for ep in endpoints]
        p95_times = [self.statistics["endpoints"][ep]["p95_response_time"]*1000 for ep in endpoints]
        
        x = range(len(endpoints))
        plt.bar(x, avg_times, width=0.4, label="Promedio", align="edge")
        plt.bar([i+0.4 for i in x], p95_times, width=0.4, label="P95", align="edge")
        plt.xticks([i+0.2 for i in x], endpoints, rotation=45, ha="right")
        plt.ylabel("Tiempo de respuesta (ms)")
        plt.title("Tiempos de respuesta por endpoint")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "response_times.png"))
        
        # Gráfico de tasas de éxito por endpoint
        plt.figure(figsize=(12, 6))
        success_rates = [self.statistics["endpoints"][ep]["success_rate"] for ep in endpoints]
        error_rates = [self.statistics["endpoints"][ep]["error_rate"] for ep in endpoints]
        
        plt.bar(x, success_rates, width=0.4, label="Éxito", align="edge")
        plt.bar([i+0.4 for i in x], error_rates, width=0.4, label="Error", align="edge")
        plt.xticks([i+0.2 for i in x], endpoints, rotation=45, ha="right")
        plt.ylabel("Porcentaje (%)")
        plt.title("Tasas de éxito y error por endpoint")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "success_rates.png"))
        
        # Guardar resultados en formato JSON
        results_file = os.path.join(charts_dir, "results.json")
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "configuration": {
                    "base_url": self.base_url,
                    "endpoints": self.endpoints,
                    "concurrency": self.concurrency,
                    "num_requests": self.num_requests,
                    "timeout": self.timeout
                },
                "statistics": self.statistics
            }, f, indent=2)
        
        print(f"\nGráficos y resultados guardados en: {charts_dir}")
        return charts_dir

def main():
    parser = argparse.ArgumentParser(description="Herramienta de pruebas de carga para la aplicación")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help=f"URL base de la aplicación (predeterminado: {DEFAULT_BASE_URL})")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help=f"Número de hilos concurrentes (predeterminado: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS, help=f"Número total de solicitudes por endpoint (predeterminado: {DEFAULT_REQUESTS})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Tiempo de espera en segundos para cada solicitud (predeterminado: {DEFAULT_TIMEOUT})")
    parser.add_argument("--endpoints", nargs="+", default=["/", "/welcome", "/tools/"], help="Lista de endpoints a probar")
    parser.add_argument("--output", default=RESULTS_DIR, help=f"Directorio para guardar los resultados (predeterminado: {RESULTS_DIR})")
    
    args = parser.parse_args()
    
    print("="*80)
    print("PRUEBA DE CARGA DE LA APLICACIÓN")
    print("="*80)
    print(f"URL base: {args.url}")
    print(f"Endpoints: {', '.join(args.endpoints)}")
    print(f"Concurrencia: {args.concurrency}")
    print(f"Solicitudes por endpoint: {args.requests}")
    print(f"Tiempo de espera: {args.timeout} segundos")
    print("="*80)
    
    # Ejecutar la prueba de carga
    load_test = LoadTest(
        base_url=args.url,
        endpoints=args.endpoints,
        concurrency=args.concurrency,
        num_requests=args.requests,
        timeout=args.timeout
    )
    
    load_test.run_test()
    load_test.print_results()
    
    # Generar gráficos
    try:
        charts_dir = load_test.generate_charts(args.output)
        print(f"Para ver los gráficos, abra los archivos PNG en: {charts_dir}")
    except Exception as e:
        print(f"Error al generar gráficos: {e}")
        print("Los gráficos requieren matplotlib. Instálelo con: pip install matplotlib")

if __name__ == "__main__":
    main()
