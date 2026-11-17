const menuButton = document.getElementById("sidebarToggle");
const sidebar = document.getElementById("sidebar");

if (menuButton && sidebar) {
  menuButton.addEventListener("click", () => {
    const isHidden = sidebar.classList.toggle("hidden");
    menuButton.setAttribute("aria-expanded", String(!isHidden));
  });
}

const copyWhatsapp = document.getElementById("copyWhatsapp");
const whatsappText = document.getElementById("whatsappText");
if (copyWhatsapp && whatsappText) {
  copyWhatsapp.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(whatsappText.value);
      copyWhatsapp.textContent = "Mensaje copiado";
    } catch (error) {
      whatsappText.focus();
      whatsappText.select();
    }
  });
}
