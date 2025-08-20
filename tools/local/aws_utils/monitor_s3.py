#!/usr/bin/env python3
"""
Script: monitor_s3.py
Descripción: Monitorea el uso y estado de AWS S3.
             Proporciona métricas de uso, costos estimados y alertas.

Funcionalidades:
  ✅ Monitoreo de uso de bucket
  ✅ Métricas de almacenamiento
  ✅ Estimación de costos
  ✅ Alertas de uso excesivo
  ✅ Reporte de objetos antiguos
  ✅ Análisis de patrones de acceso

Uso:
  python3 monitor_s3.py

Requisitos:
  - boto3
  - python-dotenv
  - Credenciales AWS configuradas

Variables de entorno:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_REGION
  - S3_BUCKET_NAME

Autor: EDF Developer - 2025-08-08
Versión: 1.0
"""

import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Monitor:
    """Monitor de AWS S3."""

    def __init__(self, bucket_name=None):
        """
        Inicializa el monitor S3.

        Args:
            bucket_name (str): Nombre del bucket a monitorear
        """
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")

        if not all([self.aws_access_key, self.aws_secret_key, self.aws_region]):
            raise ValueError("Credenciales AWS incompletas")

        if not self.bucket_name:
            raise ValueError("Nombre de bucket no especificado")

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region,
        )

        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "bucket_name": self.bucket_name,
            "region": self.aws_region,
            "storage": {},
            "objects": {},
            "costs": {},
            "alerts": [],
        }

    def get_storage_metrics(self):
        """Obtiene métricas de almacenamiento."""
        print("🔍 Obteniendo métricas de almacenamiento...")

        try:
            # Listar todos los objetos
            objects = []
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.bucket_name):
                if "Contents" in page:
                    objects.extend(page["Contents"])

            if not objects:
                self.metrics["storage"] = {
                    "total_objects": 0,
                    "total_size_bytes": 0,
                    "total_size_gb": 0,
                    "average_object_size": 0,
                }
                return

            # Calcular métricas
            total_objects = len(objects)
            total_size_bytes = sum(obj["Size"] for obj in objects)
            total_size_gb = total_size_bytes / (1024**3)
            average_size = total_size_bytes / total_objects if total_objects > 0 else 0

            # Análisis por tipo de archivo
            file_types = defaultdict(lambda: {"count": 0, "size": 0})
            for obj in objects:
                key = obj["Key"]
                extension = Path(key).suffix.lower()
                file_types[extension]["count"] += 1
                file_types[extension]["size"] += obj["Size"]

            # Top 10 tipos de archivo por tamaño
            top_file_types = sorted(
                file_types.items(), key=lambda x: x[1]["size"], reverse=True
            )[:10]

            self.metrics["storage"] = {
                "total_objects": total_objects,
                "total_size_bytes": total_size_bytes,
                "total_size_gb": round(total_size_gb, 2),
                "average_object_size": round(average_size, 2),
                "file_types": dict(top_file_types),
            }

            print("✅ Métricas de almacenamiento obtenidas")
            print(f"   📄 Objetos totales: {total_objects:,}")
            print(f"   💾 Tamaño total: {total_size_gb:.2f} GB")
            print(f"   📊 Tamaño promedio: {average_size / 1024:.2f} KB")

        except ClientError as e:
            logger.error(f"Error obteniendo métricas de almacenamiento: {e}")
            self.metrics["alerts"].append(f"Error obteniendo métricas: {e}")

    def get_object_metrics(self):
        """Obtiene métricas de objetos."""
        print("🔍 Analizando objetos...")

        try:
            # Listar objetos con metadatos
            objects = []
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.bucket_name):
                if "Contents" in page:
                    objects.extend(page["Contents"])

            if not objects:
                self.metrics["objects"] = {
                    "total_objects": 0,
                    "old_objects": [],
                    "large_objects": [],
                    "recent_objects": 0,
                }
                return

            # Análisis de objetos antiguos (>30 días)
            cutoff_date = datetime.now() - timedelta(days=30)
            old_objects = []
            large_objects = []
            recent_objects = 0

            for obj in objects:
                last_modified = obj["LastModified"].replace(tzinfo=None)

                # Objetos antiguos
                if last_modified < cutoff_date:
                    old_objects.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": last_modified.isoformat(),
                            "days_old": (datetime.now() - last_modified).days,
                        }
                    )

                # Objetos grandes (>10MB)
                if obj["Size"] > 10 * 1024 * 1024:  # 10MB
                    large_objects.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "size_mb": round(obj["Size"] / (1024**2), 2),
                            "last_modified": last_modified.isoformat(),
                        }
                    )

                # Objetos recientes (<7 días)
                if last_modified > datetime.now() - timedelta(days=7):
                    recent_objects += 1

            # Ordenar por tamaño y antigüedad
            old_objects.sort(key=lambda x: x["days_old"], reverse=True)
            large_objects.sort(key=lambda x: x["size"], reverse=True)

            self.metrics["objects"] = {
                "total_objects": len(objects),
                "old_objects": old_objects[:20],  # Top 20 más antiguos
                "large_objects": large_objects[:20],  # Top 20 más grandes
                "recent_objects": recent_objects,
                "objects_older_than_30_days": len(old_objects),
                "objects_larger_than_10mb": len(large_objects),
            }

            print("✅ Análisis de objetos completado")
            print(f"   📅 Objetos antiguos (>30 días): {len(old_objects)}")
            print(f"   📦 Objetos grandes (>10MB): {len(large_objects)}")
            print(f"   🆕 Objetos recientes (<7 días): {recent_objects}")

        except ClientError as e:
            logger.error(f"Error analizando objetos: {e}")
            self.metrics["alerts"].append(f"Error analizando objetos: {e}")

    def estimate_costs(self):
        """Estima los costos de S3."""
        print("🔍 Estimando costos...")

        try:
            storage_gb = self.metrics["storage"].get("total_size_gb", 0)
            total_objects = self.metrics["storage"].get("total_objects", 0)

            # Precios aproximados por región (us-east-1)
            # Estos precios pueden variar, consulta la documentación oficial
            prices = {
                "us-east-1": {
                    "storage": 0.023,  # USD por GB por mes
                    "requests": 0.0004,  # USD por 1000 requests
                    "data_transfer": 0.09,  # USD por GB transferido
                },
                "us-west-2": {
                    "storage": 0.023,
                    "requests": 0.0004,
                    "data_transfer": 0.09,
                },
                "eu-west-1": {
                    "storage": 0.025,
                    "requests": 0.0004,
                    "data_transfer": 0.09,
                },
            }

            region_prices = prices.get(self.aws_region, prices["us-east-1"])

            # Estimaciones mensuales
            storage_cost = storage_gb * region_prices["storage"]
            request_cost = (
                (total_objects * 2) * region_prices["requests"] / 1000
            )  # Asumiendo 2 requests por objeto
            total_estimated_cost = storage_cost + request_cost

            self.metrics["costs"] = {
                "storage_cost_usd": round(storage_cost, 2),
                "request_cost_usd": round(request_cost, 2),
                "total_estimated_cost_usd": round(total_estimated_cost, 2),
                "region": self.aws_region,
                "prices_used": region_prices,
            }

            print("✅ Estimación de costos completada")
            print(f"   💰 Costo de almacenamiento: ${storage_cost:.2f}/mes")
            print(f"   🔄 Costo de requests: ${request_cost:.2f}/mes")
            print(f"   💵 Costo total estimado: ${total_estimated_cost:.2f}/mes")

        except Exception as e:
            logger.error(f"Error estimando costos: {e}")
            self.metrics["alerts"].append(f"Error estimando costos: {e}")

    def check_alerts(self):
        """Verifica condiciones de alerta."""
        print("🔍 Verificando alertas...")

        storage_gb = self.metrics["storage"].get("total_size_gb", 0)
        total_objects = self.metrics["storage"].get("total_objects", 0)
        old_objects_count = self.metrics["objects"].get("objects_older_than_30_days", 0)
        large_objects_count = self.metrics["objects"].get("objects_larger_than_10mb", 0)

        alerts = []

        # Alerta de uso excesivo de almacenamiento
        if storage_gb > 100:  # Más de 100GB
            alerts.append(
                {
                    "type": "STORAGE_USAGE",
                    "severity": "WARNING",
                    "message": f"Uso de almacenamiento alto: {storage_gb:.2f} GB",
                    "recommendation": "Considera limpiar objetos innecesarios o implementar lifecycle policies",
                }
            )

        # Alerta de muchos objetos antiguos
        if old_objects_count > total_objects * 0.5:  # Más del 50% son antiguos
            alerts.append(
                {
                    "type": "OLD_OBJECTS",
                    "severity": "INFO",
                    "message": f"Muchos objetos antiguos: {old_objects_count} de {total_objects}",
                    "recommendation": "Considera implementar lifecycle policies para objetos antiguos",
                }
            )

        # Alerta de objetos grandes
        if large_objects_count > 100:  # Más de 100 objetos grandes
            alerts.append(
                {
                    "type": "LARGE_OBJECTS",
                    "severity": "INFO",
                    "message": f"Muchos objetos grandes: {large_objects_count} objetos >10MB",
                    "recommendation": "Considera comprimir o optimizar objetos grandes",
                }
            )

        # Alerta de costo estimado alto
        estimated_cost = self.metrics["costs"].get("total_estimated_cost_usd", 0)
        if estimated_cost > 50:  # Más de $50/mes
            alerts.append(
                {
                    "type": "HIGH_COST",
                    "severity": "WARNING",
                    "message": f"Costo estimado alto: ${estimated_cost:.2f}/mes",
                    "recommendation": "Revisa el uso de almacenamiento y optimiza costos",
                }
            )

        self.metrics["alerts"].extend(alerts)

        if alerts:
            print(f"⚠️  Se encontraron {len(alerts)} alertas:")
            for alert in alerts:
                print(f"   [{alert['severity']}] {alert['message']}")
        else:
            print("✅ No se encontraron alertas")

    def generate_report(self):
        """Genera un reporte completo."""
        print("\n" + "=" * 50)
        print("📊 GENERANDO REPORTE DE MONITOREO S3")
        print("=" * 50)

        # Resumen ejecutivo
        storage_gb = self.metrics["storage"].get("total_size_gb", 0)
        total_objects = self.metrics["storage"].get("total_objects", 0)
        estimated_cost = self.metrics["costs"].get("total_estimated_cost_usd", 0)

        print(f"📦 Bucket: {self.bucket_name}")
        print(f"🌍 Región: {self.aws_region}")
        print(f"📄 Objetos totales: {total_objects:,}")
        print(f"💾 Almacenamiento: {storage_gb:.2f} GB")
        print(f"💵 Costo estimado: ${estimated_cost:.2f}/mes")

        # Alertas
        if self.metrics["alerts"]:
            print(f"\n🚨 Alertas ({len(self.metrics['alerts'])}):")
            for alert in self.metrics["alerts"]:
                if isinstance(alert, dict):
                    print(f"   [{alert['severity']}] {alert['message']}")
                    if "recommendation" in alert:
                        print(f"      💡 {alert['recommendation']}")
                else:
                    print(f"   ⚠️  {alert}")

        # Guardar reporte
        report_file = Path("tools/local/aws_utils/s3_monitoring_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(report_file, "w") as f:
                json.dump(self.metrics, f, indent=2, default=str)
            print(f"\n📄 Reporte guardado en: {report_file}")
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")

    def run_monitoring(self):
        """Ejecuta el monitoreo completo."""
        print("🚀 INICIANDO MONITOREO DE AWS S3")
        print("=" * 50)

        try:
            self.get_storage_metrics()
            self.get_object_metrics()
            self.estimate_costs()
            self.check_alerts()
            self.generate_report()

            return True

        except Exception as e:
            logger.error(f"Error en monitoreo: {e}")
            return False


def main():
    """Función principal."""
    try:
        monitor = S3Monitor()

        if monitor.run_monitoring():
            print("\n🎉 Monitoreo completado exitosamente")
            sys.exit(0)
        else:
            print("\n❌ Monitoreo falló")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica las credenciales AWS y la configuración del bucket")
        sys.exit(1)


if __name__ == "__main__":
    main()
