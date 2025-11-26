// Atualiza o ano do footer
(function () {
  const y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();
})();

// Equalizer full-width no rodapé (responsivo)
function renderEq() {
  const eq = document.getElementById('eq');
  if (!eq) return;
  eq.innerHTML = '';

  const barWidth = 7, gap = 8, pad = 28 * 2;
  const vw = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
  const total = Math.max(8, Math.ceil((vw - pad) / (barWidth + gap)));
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  for (let i = 0; i < total; i++) {
    const bar = document.createElement('span');
    bar.className = 'hm-eq__bar';
    if (!prefersReduced) {
      const base = 2.4;
      bar.style.animationDelay = `${(i * 0.035).toFixed(3)}s`;
      bar.style.animationDuration = `${(base + (i % 9) * 0.08).toFixed(2)}s`;
    }
    eq.appendChild(bar);
  }
}
window.addEventListener('DOMContentLoaded', renderEq);
window.addEventListener('resize', () => {
  clearTimeout(window.__eq_raf);
  window.__eq_raf = setTimeout(renderEq, 120);
});

// Toggle visual da senha (login)
(function () {
  const toggle = document.getElementById('togglePwd');
  const pwd = document.getElementById('password');
  if (!toggle || !pwd) return;
  toggle.addEventListener('click', () => {
    const type = pwd.getAttribute('type') === 'password' ? 'text' : 'password';
    pwd.setAttribute('type', type);
    toggle.textContent = type === 'password' ? '👁️' : '✕';
  });
})();

// Carrossel simples (setas)
(function () {
  const btns = document.querySelectorAll('.hm-scroll-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const dir = btn.dataset.dir === 'left' ? -1 : 1;
      const container = btn.parentElement.querySelector('.hm-scroll-container');
      if (!container) return;
      const amount = Math.floor(container.clientWidth * 0.8);
      container.scrollBy({ left: amount * dir, behavior: 'smooth' });
    });
  });
})();

// Redireciona o artista para o CRUD de músicas
const uploadBtn = document.getElementById("uploadSongBtn");
if (uploadBtn) {
  uploadBtn.addEventListener("click", () => {
    window.location.href = "{{ url_for('crud_msc') }}";
  });
}

// ---- MENU DO USUÁRIO ----
const userMenuToggle = document.getElementById("userMenuToggle");
const userMenu = document.getElementById("userMenu");

if (userMenuToggle) {
    userMenuToggle.addEventListener("click", (e) => {
        e.stopPropagation(); // evita fechar ao clicar no próprio menu
        userMenu.classList.toggle("visible");
    });

    // Fechar ao clicar fora
    document.addEventListener("click", () => {
        userMenu.classList.remove("visible");
    });
}

document.addEventListener("DOMContentLoaded", () => {
  const carousels = document.querySelectorAll(".hm-carousel");

  carousels.forEach(carousel => {
      const container = carousel.querySelector(".hm-scroll-container");
      const btnLeft = carousel.querySelector(".hm-scroll-btn.left");
      const btnRight = carousel.querySelector(".hm-scroll-btn.right");

      btnLeft.addEventListener("click", () => {
          container.scrollBy({ left: -300, behavior: "smooth" });
      });

      btnRight.addEventListener("click", () => {
          container.scrollBy({ left: 300, behavior: "smooth" });
      });
  });
});

function openAdmin(section) {
  const panels = ["users", "uploads", "stats"];
  panels.forEach(p => {
    document.getElementById(`admin-${p}`).style.display = "none";
  });

  document.getElementById(`admin-${section}`).style.display = "block";
}

function openEditModal(id, first, last, nick, role) {
  document.getElementById("edit_id").value = id;
  document.getElementById("edit_first").value = first;
  document.getElementById("edit_last").value = last;
  document.getElementById("edit_nick").value = nick;
  document.getElementById("edit_role").value = role;

  document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("editModal").style.display = "none";
}

function openDeleteModal(id, nickname) {
  document.getElementById("delete_id").value = id;
  document.getElementById("deleteUserNick").innerText = nickname;

  document.getElementById("deleteModal").style.display = "flex";
}

function closeDeleteModal() {
  document.getElementById("deleteModal").style.display = "none";
}