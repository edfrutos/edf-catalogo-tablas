// JS específico para la página de testing interactivo
document.addEventListener("DOMContentLoaded", function () {
  if (window.__testingJSLoaded) return;
  window.__testingJSLoaded = true;

  // Generador de plantilla de test
  const genForm = document.getElementById("test-template-generator-form");
  const nameInput = document.getElementById("model-endpoint-name");
  const codeBlock = document.getElementById("generated-template-code");
  const templateBlock = document.getElementById("generated-template-block");
  const copyBtn = document.getElementById("copy-template-btn");

  function bindTemplateListeners() {
    genForm && genForm.removeEventListener("submit", genForm._submit);
    genForm._submit = async function(e) {
      e.preventDefault();
      const name = nameInput.value.trim();
      if (!name) return;
      codeBlock.textContent = "Generando...";
      templateBlock.style.display = "block";
      try {
        const resp = await fetch("/dev-template/generate-test-template", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({name})
        });
        const data = await resp.json();
        if (data.success) {
          codeBlock.textContent = data.code;
        } else {
          codeBlock.textContent = "Error: " + (data.error || "No se pudo generar la plantilla.");
        }
      } catch (_) { // eslint-disable-line no-unused-vars
        codeBlock.textContent = "Error de red o backend.";
      }
    };
    genForm && genForm.addEventListener("submit", genForm._submit);

    copyBtn && copyBtn.removeEventListener("click", copyBtn._click);
    copyBtn._click = function() {
      if (codeBlock.textContent) {
        navigator.clipboard.writeText(codeBlock.textContent);
      }
    };
    copyBtn && copyBtn.addEventListener("click", copyBtn._click);
  }

  bindTemplateListeners();

  // Botones de ejecución de test
  document.querySelectorAll(".run-test-btn").forEach(function(btn) {
    btn.removeEventListener("click", btn._runClick);
    btn._runClick = function() {
      const testFile = btn.getAttribute("data-test");
      window.runTest(testFile);
    };
    btn.addEventListener("click", btn._runClick);
  });

  // Botón de parámetros abre el modal
  let selectedScript = "";
  let selectedScriptName = "";
  document.querySelectorAll(".params-btn").forEach(function(btn) {
    btn.removeEventListener("click", btn._paramsClick);
    btn._paramsClick = async function() {
      selectedScript = btn.getAttribute("data-script");
      selectedScriptName = btn.getAttribute("data-scriptname");
      document.getElementById("paramsScriptName").textContent = selectedScriptName;
      document.getElementById("paramsInput").value = "";
      // Nueva lógica: mostrar ayuda de parámetros
      const helpBlock = document.getElementById("paramsHelpBlock");
      helpBlock.textContent = "Cargando ayuda...";
      try {
        const resp = await fetch("/dev-template/api/script-params-help", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ script_path: selectedScript })
        });
        const data = await resp.json();
        if (data.success) {
          helpBlock.textContent = data.help;
        } else {
          helpBlock.textContent = data.error || "No se pudo obtener ayuda.";
        }
      } catch (_) { // eslint-disable-line no-unused-vars
        helpBlock.textContent = "Error obteniendo ayuda de parámetros.";
      }
      console.log("[DEBUG] Pulsado botón parámetros para", selectedScriptName, selectedScript);
      var modalEl = document.getElementById("paramsModal");
      if (!modalEl) { console.error("No se encuentra el modal paramsModal"); return; }
      if (typeof bootstrap === "undefined" || !bootstrap.Modal) { console.error("Bootstrap Modal no está disponible"); return; }
      let paramsModal = new bootstrap.Modal(modalEl);
      paramsModal.show();
    };
    btn.addEventListener("click", btn._paramsClick);
  });

  // Ejecutar con parámetros
  document.getElementById("runWithParamsBtn").addEventListener("click", function() {
    let params = document.getElementById("paramsInput").value.trim();
    if (!selectedScript) return;
    window.runTest(selectedScript, params);
    bootstrap.Modal.getInstance(document.getElementById("paramsModal")).hide();
  });

  // Función global para ejecutar test
  window.runTest = function(script, params = "") {
    let data = { test_file: script };
    if (params) data.params = params;
    fetch("/dev-template/run-test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(res => {
      showScriptResultModal(res.result || res.error || "Sin salida", "Resultado de Test/Script"); // eslint-disable-line no-undef
    })
    .catch(err => {
      showScriptResultModal("Error ejecutando test: " + err, "Error"); // eslint-disable-line no-undef
    });
  };

  // Botón para actualizar README de tests (solo admin)
  const updateReadmeBtn = document.getElementById("update-tests-readme-btn");
  if (updateReadmeBtn) {
    updateReadmeBtn.addEventListener("click", async function() {
      const alertDiv = document.getElementById("update-readme-alert");
      if (!alertDiv) {
        console.error("[update-tests-readme-btn] No se encontró el div de alerta (#update-readme-alert)");
        return;
      }
      alertDiv.style.display = "block";
      alertDiv.innerHTML = "<div class=\"alert alert-info mb-2\">Actualizando README de tests...</div>";
      try {
        const resp = await fetch("/dev-template/api/update-tests-readme", { method: "POST" });
        const data = await resp.json();
        if (data.success) {
          alertDiv.innerHTML = "<div class=\"alert alert-success mb-2\">" + (data.message || "README actualizado.") + "</div>";
        } else {
          alertDiv.innerHTML = "<div class=\"alert alert-danger mb-2\">" + (data.error || "Error actualizando README.") + "</div>";
        }
      } catch (_) { // eslint-disable-line no-unused-vars
        alertDiv.innerHTML = "<div class=\"alert alert-danger mb-2\">Error de red o backend al actualizar README.</div>";
      }
      setTimeout(() => { alertDiv.style.display = "none"; }, 3500);
    });
  } else {
    console.warn("[update-tests-readme-btn] No se encontró el botón en el DOM");
  }

  // Botón de ejecutar todos los tests
  document.getElementById("run-all-tests").addEventListener("click", function() {
    window.runTest("");
  });
});
// Modal para mostrar resultados de test/script
window.showScriptResultModal = function(content, title = "Resultado") {
  let modalId = "scriptResultModal";
  let modalEl = document.getElementById(modalId);
  if (!modalEl) {
    // Crea el modal si no existe
    modalEl = document.createElement("div");
    modalEl.className = "modal fade";
    modalEl.id = modalId;
    modalEl.tabIndex = -1;
    modalEl.innerHTML = `
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"></h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
          </div>
          <div class="modal-body">
            <pre class="mb-0" style="white-space:pre-wrap;word-break:break-all;"></pre>
          </div>
        </div>
      </div>`;
    document.body.appendChild(modalEl);
  }
  modalEl.querySelector(".modal-title").textContent = title;
  modalEl.querySelector("pre").textContent = content;
  let modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();
};