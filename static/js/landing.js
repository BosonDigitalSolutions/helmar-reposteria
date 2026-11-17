(function () {
  const whatsappNumber = document.body.dataset.whatsapp || "";
  const menuButton = document.getElementById("menuBtn");
  const navLinks = document.getElementById("navLinks");
  const catalogModal = document.getElementById("catalogModal");
  const grid = document.getElementById("products");
  const search = document.getElementById("search");
  const filters = document.getElementById("filters");
  const dataNode = document.getElementById("catalog-data");
  let products = [];
  let active = "todos";
  let lastFocus = null;

  if (dataNode) {
    try {
      products = JSON.parse(dataNode.textContent || "[]");
    } catch (error) {
      products = [];
    }
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));
  }

  function safeUrl(value) {
    if (typeof value !== "string") return "";
    if (value.startsWith("/") || value.startsWith("https://") || value.startsWith("http://")) {
      return value;
    }
    return "";
  }

  function openWhatsApp(customMessage) {
    if (!/^\d{10,15}$/.test(whatsappNumber)) {
      window.alert("Para activar WhatsApp, configura HELYMAR_WHATSAPP_NUMBER en el archivo .env con el número internacional, sin + ni espacios.");
      return;
    }
    const message = customMessage || "Hola, HelyMar 🍒. Quiero solicitar una cotización.";
    window.open(
      "https://wa.me/" + whatsappNumber + "?text=" + encodeURIComponent(message),
      "_blank",
      "noopener,noreferrer"
    );
  }

  function render() {
    if (!grid) return;
    if (!products.length) {
      grid.innerHTML = '<p class="empty">El catálogo se publicará aquí cuando haya productos reales.</p>';
      return;
    }
    const term = search ? search.value.trim().toLocaleLowerCase("es") : "";
    const shown = products.filter((product) => {
      const category = String(product.category || "");
      const haystack = (String(product.name || "") + " " + String(product.description || "")).toLocaleLowerCase("es");
      return (active === "todos" || category === active) && haystack.includes(term);
    });
    if (!shown.length) {
      grid.innerHTML = '<p class="empty">No encontramos productos con esos filtros. Prueba otra búsqueda.</p>';
      return;
    }
    grid.innerHTML = shown.map((product) => {
      const name = escapeHtml(product.name);
      const description = escapeHtml(product.description);
      const category = escapeHtml(product.category_name || product.category);
      const image = safeUrl(product.image);
      const imageHtml = image ? `<img src="${escapeHtml(image)}" alt="${name}" loading="lazy">` : "";
      const price = product.price_label ? `<p class="tag">${escapeHtml(product.price_label)}</p>` : "";
      const custom = product.customizable ? '<span class="tag">Personalizable</span>' : "";
      const presentations = (product.presentations || []).map(escapeHtml).join(", ");
      const presentationsHtml = presentations ? `<p>${presentations}</p>` : "";
      return `<article class="product">${imageHtml}<div class="product-body"><span class="tag">${category}</span>${custom}<h3>${name}</h3><p>${description}</p>${presentationsHtml}${price}<button type="button" class="btn" data-quote="${escapeHtml(product.id)}">Cotizar este producto ↗</button></div></article>`;
    }).join("");
  }

  function focusable(root) {
    return [...root.querySelectorAll("a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled])")]
      .filter((element) => !element.hasAttribute("hidden"));
  }

  function openCatalog(trigger) {
    if (!catalogModal) return;
    lastFocus = trigger || document.activeElement;
    if (navLinks) navLinks.classList.remove("open");
    if (menuButton) menuButton.setAttribute("aria-expanded", "false");
    catalogModal.showModal();
    const closeButton = document.getElementById("closeCatalog");
    if (closeButton) closeButton.focus();
  }

  if (menuButton && navLinks) {
    menuButton.addEventListener("click", (event) => {
      event.stopPropagation();
      const open = navLinks.classList.toggle("open");
      menuButton.setAttribute("aria-expanded", String(open));
    });
    navLinks.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        navLinks.classList.remove("open");
        menuButton.setAttribute("aria-expanded", "false");
      }
    });
  }

  const loginModal = document.getElementById("loginModal");
  document.querySelectorAll("[data-open-login]").forEach((element) => {
    element.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!loginModal) {
        window.location.href = element.getAttribute("href");
        return;
      }
      if (navLinks) navLinks.classList.remove("open");
      if (menuButton) menuButton.setAttribute("aria-expanded", "false");
      loginModal.showModal();
      const field = loginModal.querySelector("input[name='username']");
      if (field) field.focus();
    });
  });
  if (loginModal) {
    const closeLogin = loginModal.querySelector("[data-close-login]");
    if (closeLogin) closeLogin.addEventListener("click", () => loginModal.close());
    loginModal.addEventListener("click", (event) => {
      if (event.target === loginModal) loginModal.close();
    });
  }

  document.querySelectorAll("a[data-whatsapp], button[data-whatsapp]").forEach((element) => {
    element.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openWhatsApp();
    });
  });

  document.querySelectorAll("[data-open-catalog]").forEach((element) => {
    element.addEventListener("click", (event) => {
      event.preventDefault();
      openCatalog(element);
    });
  });

  if (filters) {
    filters.addEventListener("click", (event) => {
      const button = event.target.closest("[data-filter]");
      if (!button) return;
      active = button.dataset.filter;
      filters.querySelectorAll(".filter").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      render();
    });
  }

  if (search) search.addEventListener("input", render);

  if (grid) {
    grid.addEventListener("click", (event) => {
      const button = event.target.closest("[data-quote]");
      if (!button) return;
      const product = products.find((item) => String(item.id) === button.dataset.quote);
      if (!product) return;
      const message = "Hola, HelyMar 🍒. Quiero cotizar " + product.name + ". ¿Podrían darme información sobre opciones de personalización, precio y disponibilidad?";
      if (catalogModal) catalogModal.close();
      openWhatsApp(message);
    });
  }

  if (catalogModal) {
    const closeButton = document.getElementById("closeCatalog");
    if (closeButton) closeButton.addEventListener("click", () => catalogModal.close());
    catalogModal.addEventListener("click", (event) => {
      if (event.target === catalogModal) catalogModal.close();
    });
    catalogModal.addEventListener("close", () => {
      if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
    });
    catalogModal.addEventListener("keydown", (event) => {
      if (event.key !== "Tab") return;
      const items = focusable(catalogModal);
      if (!items.length) {
        event.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function snapTargets() {
    return [...document.querySelectorAll("main .snap-panel, footer.footer")];
  }

  function nearestIndex(targets) {
    const marker = window.innerHeight * 0.45;
    let index = 0;
    targets.forEach((panel, position) => {
      if (panel.getBoundingClientRect().top <= marker) index = position;
    });
    return index;
  }

  let snapLock = false;

  function moveToIndex(index, moveFocus) {
    const targets = snapTargets();
    if (!targets.length) return;
    const next = Math.max(0, Math.min(targets.length - 1, index));
    if (snapLock || next === nearestIndex(targets)) return;
    snapLock = true;
    if (navLinks) navLinks.classList.remove("open");
    if (menuButton) menuButton.setAttribute("aria-expanded", "false");
    targets[next].scrollIntoView({ behavior: "auto", block: "start" });
    if (moveFocus) {
      const heading = targets[next].querySelector("h1, h2");
      if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
      }
    }
    window.setTimeout(() => {
      snapLock = false;
    }, prefersReducedMotion() ? 40 : 700);
  }

  function canScrollInside(target, deltaY) {
    if (!deltaY || !target || !target.closest) return false;
    let node = target.nodeType === 1 ? target : target.parentElement;
    if (!node || !node.closest) return false;
    const boundary = node.closest(".snap-panel, .footer, .catalog-modal");
    while (node && node !== document.body) {
      const overflowY = window.getComputedStyle(node).overflowY;
      const scrollable = overflowY === "auto" || overflowY === "scroll";
      if (scrollable && node.scrollHeight > node.clientHeight + 2) {
        const atEnd = node.scrollTop + node.clientHeight >= node.scrollHeight - 2;
        const atStart = node.scrollTop <= 2;
        if (deltaY > 0 && !atEnd) return true;
        if (deltaY < 0 && !atStart) return true;
      }
      if (node === boundary) break;
      node = node.parentElement;
    }
    return false;
  }

  document.addEventListener("keydown", (event) => {
    const keys = ["ArrowDown", "PageDown", "ArrowUp", "PageUp", "Home", "End"];
    if (!keys.includes(event.key) || event.altKey || event.ctrlKey || event.metaKey) return;
    if (catalogModal && catalogModal.open) return;
    if (document.body.classList.contains("page-plain")) return;
    const tag = document.activeElement ? document.activeElement.tagName : "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    const targets = snapTargets();
    if (!targets.length) return;
    let index = nearestIndex(targets);
    if (event.key === "Home") index = 0;
    else if (event.key === "End") index = targets.length - 1;
    else if (event.key === "ArrowDown" || event.key === "PageDown") index += 1;
    else index -= 1;
    event.preventDefault();
    moveToIndex(index, true);
  });

  if (!document.body.classList.contains("page-plain") && !prefersReducedMotion()) {
    window.addEventListener("wheel", (event) => {
      if (catalogModal && catalogModal.open) return;
      if (event.ctrlKey) return;
      if (event.target.closest && event.target.closest("a, button, input, textarea, select, .catalog-modal")) return;
      let delta = event.deltaY;
      if (event.deltaMode === 1) delta *= 16;
      if (event.deltaMode === 2) delta *= window.innerHeight;
      if (!delta || canScrollInside(event.target, delta)) return;
      event.preventDefault();
      if (snapLock) return;
      const direction = delta > 0 ? 1 : -1;
      moveToIndex(nearestIndex(snapTargets()) + direction, false);
    }, { passive: false });

    let touchStartY = null;
    window.addEventListener("touchstart", (event) => {
      if (event.touches.length !== 1) {
        touchStartY = null;
        return;
      }
      touchStartY = event.touches[0].clientY;
    }, { passive: true });
    window.addEventListener("touchmove", (event) => {
      if (touchStartY === null || (catalogModal && catalogModal.open)) return;
      const delta = touchStartY - event.touches[0].clientY;
      if (Math.abs(delta) < 10 || canScrollInside(event.target, delta)) return;
      event.preventDefault();
    }, { passive: false });
    window.addEventListener("touchend", (event) => {
      if (touchStartY === null) return;
      const delta = touchStartY - event.changedTouches[0].clientY;
      touchStartY = null;
      if (catalogModal && catalogModal.open) return;
      if (Math.abs(delta) < 48 || canScrollInside(event.target, delta)) return;
      moveToIndex(nearestIndex(snapTargets()) + (delta > 0 ? 1 : -1), false);
    }, { passive: true });
  }

  render();
})();
