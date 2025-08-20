#!/usr/bin/env python3
"""
Script: diagnose_s3_permissions.py
Descripción: Diagnostica permisos y problemas de acceso a AWS S3.
             Verifica credenciales, permisos de bucket y conectividad.

Funcionalidades:
  ✅ Diagnóstico de credenciales AWS
  ✅ Verificación de permisos S3
  ✅ Test de conectividad
  ✅ Análisis de políticas de bucket
  ✅ Reporte detallado de problemas

Uso:
  python3 diagnose_s3_permissions.py

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
import os
import sys
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class S3Diagnostic:
    """Diagnóstico de permisos y problemas de S3."""

    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_client = None
        self.sts_client = None
        self.iam_client = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "issues": [],
            "recommendations": [],
        }

    def _get_error_code(self, e):
        """Obtiene el código de error de forma segura desde ClientError."""
        try:
            return e.response.get("Error", {}).get("Code")
        except (KeyError, TypeError, AttributeError):
            return None

    def log_test(self, test_name, status, message, details=None):
        """Registra el resultado de una prueba."""
        self.results["tests"][test_name] = {
            "status": status,
            "message": message,
            "details": details,
        }

        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")

    def log_issue(self, issue, severity="WARNING"):
        """Registra un problema encontrado."""
        self.results["issues"].append(
            {
                "issue": issue,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(f"🚨 {severity}: {issue}")

    def log_recommendation(self, recommendation):
        """Registra una recomendación."""
        self.results["recommendations"].append(recommendation)
        print(f"💡 Recomendación: {recommendation}")

    def test_credentials_existence(self):
        """Prueba que las credenciales estén configuradas."""
        print("🔍 Verificando existencia de credenciales...")

        missing_creds = []
        if not self.aws_access_key:
            missing_creds.append("AWS_ACCESS_KEY_ID")
        if not self.aws_secret_key:
            missing_creds.append("AWS_SECRET_ACCESS_KEY")
        if not self.aws_region:
            missing_creds.append("AWS_REGION")

        if missing_creds:
            self.log_test(
                "credentials_existence",
                "FAIL",
                f"Credenciales faltantes: {', '.join(missing_creds)}",
            )
            self.log_issue(
                f"Variables de entorno faltantes: {', '.join(missing_creds)}",
                "CRITICAL",
            )
            return False
        else:
            self.log_test(
                "credentials_existence",
                "PASS",
                "Todas las credenciales están configuradas",
            )
            return True

    def test_credentials_validity(self):
        """Prueba que las credenciales sean válidas."""
        print("🔍 Verificando validez de credenciales...")

        try:
            self.sts_client = boto3.client(
                "sts",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region,
            )

            identity = self.sts_client.get_caller_identity()

            self.log_test(
                "credentials_validity",
                "PASS",
                f"Credenciales válidas - Usuario: {identity['Arn']}",
            )

            # Verificar si es un usuario IAM o un rol
            if "user" in identity["Arn"]:
                self.log_recommendation(
                    "Considera usar roles IAM en lugar de usuarios para mayor seguridad"
                )

            return True

        except NoCredentialsError:
            self.log_test(
                "credentials_validity", "FAIL", "No se pudieron encontrar credenciales"
            )
            self.log_issue("Credenciales AWS no encontradas", "CRITICAL")
            return False
        except ClientError as e:
            # Manejar el error de forma segura verificando las claves
            error_code = None
            try:
                error_code = e.response.get("Error", {}).get("Code")
            except (KeyError, TypeError):
                pass

            if error_code == "InvalidClientTokenId":
                self.log_test("credentials_validity", "FAIL", "Access Key ID inválida")
                self.log_issue("AWS_ACCESS_KEY_ID es inválida", "CRITICAL")
            elif error_code == "SignatureDoesNotMatch":
                self.log_test(
                    "credentials_validity", "FAIL", "Secret Access Key inválida"
                )
                self.log_issue("AWS_SECRET_ACCESS_KEY es inválida", "CRITICAL")
            else:
                self.log_test(
                    "credentials_validity",
                    "FAIL",
                    f"Error de autenticación: {error_code}",
                )
                self.log_issue(f"Error de autenticación AWS: {error_code}", "CRITICAL")
            return False

    def test_s3_client_initialization(self):
        """Prueba la inicialización del cliente S3."""
        print("🔍 Verificando inicialización del cliente S3...")

        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region,
            )

            self.log_test(
                "s3_client_initialization",
                "PASS",
                "Cliente S3 inicializado correctamente",
            )
            return True

        except Exception as e:
            self.log_test(
                "s3_client_initialization",
                "FAIL",
                f"Error inicializando cliente S3: {e}",
            )
            self.log_issue(f"Error inicializando cliente S3: {e}", "CRITICAL")
            return False

    def test_s3_list_buckets_permission(self):
        """Prueba el permiso para listar buckets."""
        print("🔍 Verificando permiso para listar buckets...")

        try:
            response = self.s3_client.list_buckets()
            bucket_count = len(response["Buckets"])

            self.log_test(
                "s3_list_buckets_permission",
                "PASS",
                f"Permiso de listar buckets OK - {bucket_count} buckets encontrados",
            )

            # Listar buckets para referencia
            bucket_names = [bucket["Name"] for bucket in response["Buckets"]]
            self.results["tests"]["s3_list_buckets_permission"]["details"] = {
                "bucket_count": bucket_count,
                "bucket_names": bucket_names,
            }

            return True

        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "AccessDenied":
                self.log_test(
                    "s3_list_buckets_permission",
                    "FAIL",
                    "Acceso denegado para listar buckets",
                )
                self.log_issue("Falta permiso s3:ListAllMyBuckets", "CRITICAL")
                self.log_recommendation(
                    "Agrega el permiso s3:ListAllMyBuckets a tu usuario/rol IAM"
                )
            else:
                self.log_test(
                    "s3_list_buckets_permission",
                    "FAIL",
                    f"Error listando buckets: {error_code}",
                )
                self.log_issue(f"Error listando buckets S3: {error_code}", "CRITICAL")
            return False

    def test_bucket_access(self):
        """Prueba el acceso al bucket configurado."""
        if not self.s3_bucket_name:
            self.log_test("bucket_access", "SKIP", "S3_BUCKET_NAME no configurado")
            return True

        print(f"🔍 Verificando acceso al bucket: {self.s3_bucket_name}")

        try:
            # Verificar si el bucket existe
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)

            self.log_test(
                "bucket_access", "PASS", f"Acceso al bucket '{self.s3_bucket_name}' OK"
            )
            return True

        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "404":
                self.log_test(
                    "bucket_access", "FAIL", f"Bucket '{self.s3_bucket_name}' no existe"
                )
                self.log_issue(
                    f"Bucket S3 '{self.s3_bucket_name}' no existe", "CRITICAL"
                )
                self.log_recommendation(
                    f"Crea el bucket '{self.s3_bucket_name}' o verifica el nombre"
                )
            elif error_code == "403":
                self.log_test(
                    "bucket_access",
                    "FAIL",
                    f"Acceso denegado al bucket '{self.s3_bucket_name}'",
                )
                self.log_issue(
                    f"Sin permisos para acceder al bucket '{self.s3_bucket_name}'",
                    "CRITICAL",
                )
                self.log_recommendation(
                    "Verifica los permisos de tu usuario/rol IAM para este bucket"
                )
            else:
                self.log_test(
                    "bucket_access", "FAIL", f"Error accediendo al bucket: {error_code}"
                )
                self.log_issue(
                    f"Error accediendo al bucket S3: {error_code}", "CRITICAL"
                )
            return False

    def test_bucket_permissions(self):
        """Prueba permisos específicos en el bucket."""
        if not self.s3_bucket_name:
            self.log_test("bucket_permissions", "SKIP", "S3_BUCKET_NAME no configurado")
            return True

        print(f"🔍 Verificando permisos en bucket: {self.s3_bucket_name}")

        test_key = "diagnostic_test.txt"
        test_content = "Test de diagnóstico S3"

        permissions_tested = []

        # Test de escritura
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket_name, Key=test_key, Body=test_content
            )
            permissions_tested.append("PUT")
        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "AccessDenied":
                self.log_issue(
                    f"Sin permiso de escritura en bucket '{self.s3_bucket_name}'",
                    "CRITICAL",
                )
            else:
                self.log_issue(f"Error en test de escritura: {error_code}", "WARNING")

        # Test de lectura
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket_name, Key=test_key
            )
            content = response["Body"].read().decode("utf-8")
            if content == test_content:
                permissions_tested.append("GET")
        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "AccessDenied":
                self.log_issue(
                    f"Sin permiso de lectura en bucket '{self.s3_bucket_name}'",
                    "CRITICAL",
                )
            else:
                self.log_issue(f"Error en test de lectura: {error_code}", "WARNING")

        # Test de eliminación
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=test_key)
            permissions_tested.append("DELETE")
        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "AccessDenied":
                self.log_issue(
                    f"Sin permiso de eliminación en bucket '{self.s3_bucket_name}'",
                    "WARNING",
                )
            else:
                self.log_issue(f"Error en test de eliminación: {error_code}", "WARNING")

        if len(permissions_tested) == 3:
            self.log_test(
                "bucket_permissions",
                "PASS",
                f"Todos los permisos básicos OK: {', '.join(permissions_tested)}",
            )
        elif len(permissions_tested) > 0:
            self.log_test(
                "bucket_permissions",
                "PARTIAL",
                f"Permisos parciales: {', '.join(permissions_tested)}",
            )
        else:
            self.log_test(
                "bucket_permissions", "FAIL", "Sin permisos básicos en el bucket"
            )

        return len(permissions_tested) > 0

    def test_bucket_policy(self):
        """Analiza la política del bucket."""
        if not self.s3_bucket_name:
            self.log_test("bucket_policy", "SKIP", "S3_BUCKET_NAME no configurado")
            return True

        print(f"🔍 Analizando política del bucket: {self.s3_bucket_name}")

        try:
            response = self.s3_client.get_bucket_policy(Bucket=self.s3_bucket_name)
            policy = json.loads(response["Policy"])

            self.log_test("bucket_policy", "PASS", "Política de bucket encontrada")

            # Analizar la política
            statements = policy.get("Statement", [])
            public_access = False

            for statement in statements:
                if statement.get(
                    "Principal"
                ) == "*" and "s3:GetObject" in statement.get("Action", []):
                    public_access = True
                    break

            if public_access:
                self.log_issue("Bucket tiene acceso público de lectura", "WARNING")
                self.log_recommendation(
                    "Considera restringir el acceso público si no es necesario"
                )

            return True

        except ClientError as e:
            error_code = self._get_error_code(e)
            if error_code == "NoSuchBucketPolicy":
                self.log_test(
                    "bucket_policy", "INFO", "Bucket no tiene política configurada"
                )
                self.log_recommendation(
                    "Considera configurar una política de bucket para mayor seguridad"
                )
            else:
                self.log_test(
                    "bucket_policy", "FAIL", f"Error obteniendo política: {error_code}"
                )
            return True  # No es crítico

    def generate_report(self):
        """Genera un reporte detallado."""
        print("\n" + "=" * 50)
        print("📊 GENERANDO REPORTE DE DIAGNÓSTICO")
        print("=" * 50)

        # Contar resultados
        total_tests = len(self.results["tests"])
        passed_tests = sum(
            1 for test in self.results["tests"].values() if test["status"] == "PASS"
        )
        failed_tests = sum(
            1 for test in self.results["tests"].values() if test["status"] == "FAIL"
        )
        skipped_tests = sum(
            1 for test in self.results["tests"].values() if test["status"] == "SKIP"
        )

        print("📈 Resumen de pruebas:")
        print(f"   Total: {total_tests}")
        print(f"   ✅ Exitosas: {passed_tests}")
        print(f"   ❌ Fallidas: {failed_tests}")
        print(f"   ⏭️  Omitidas: {skipped_tests}")

        if self.results["issues"]:
            print(f"\n🚨 Problemas encontrados ({len(self.results['issues'])}):")
            for issue in self.results["issues"]:
                print(f"   [{issue['severity']}] {issue['issue']}")

        if self.results["recommendations"]:
            print(f"\n💡 Recomendaciones ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"   {i}. {rec}")

        # Guardar reporte
        report_file = Path("tools/local/aws_utils/s3_diagnostic_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(report_file, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Reporte guardado en: {report_file}")
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")

        return failed_tests == 0

    def run_diagnostic(self):
        """Ejecuta el diagnóstico completo."""
        print("🚀 INICIANDO DIAGNÓSTICO DE AWS S3")
        print("=" * 50)

        tests = [
            self.test_credentials_existence,
            self.test_credentials_validity,
            self.test_s3_client_initialization,
            self.test_s3_list_buckets_permission,
            self.test_bucket_access,
            self.test_bucket_permissions,
            self.test_bucket_policy,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_issue(f"Error ejecutando prueba: {e}", "ERROR")

        return self.generate_report()


def main():
    """Función principal."""
    diagnostic = S3Diagnostic()

    if diagnostic.run_diagnostic():
        print("\n🎉 Diagnóstico completado - No se encontraron problemas críticos")
        sys.exit(0)
    else:
        print(
            "\n⚠️  Diagnóstico completado - Se encontraron problemas que requieren atención"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
