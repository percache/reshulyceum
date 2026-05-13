(function () {
  const token = localStorage.getItem('token');
  const profile = document.getElementById('nav-profile');
  const admin = document.getElementById('nav-admin');
  const login = document.getElementById('nav-login');
  const reg = document.getElementById('nav-register');
  const logout = document.getElementById('nav-logout');
  const homeRegister = document.getElementById('home-register');
  const homeProfile = document.getElementById('home-profile');
  const homeStart = document.getElementById('home-start');

  function showLoggedIn(me) {
    login && (login.style.display = 'none');
    reg && (reg.style.display = 'none');
    logout && (logout.style.display = 'inline');
    profile && (profile.style.display = 'inline');
    homeRegister && (homeRegister.style.display = 'none');
    homeProfile && (homeProfile.style.display = 'inline-block');
    if (homeStart) homeStart.innerHTML = '<i class="fa-solid fa-list-check"></i> Продолжить решать';
    if (me && me.is_admin && admin) admin.style.display = 'inline';
  }

  function showLoggedOut() {
    login && (login.style.display = 'inline');
    reg && (reg.style.display = 'inline');
    logout && (logout.style.display = 'none');
    profile && (profile.style.display = 'none');
    admin && (admin.style.display = 'none');
    homeRegister && (homeRegister.style.display = 'inline-block');
    homeProfile && (homeProfile.style.display = 'none');
  }

  if (token) {
    showLoggedIn(null);
    fetch('/api/auth/me', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.ok ? r.json() : null)
      .then(me => {
        if (!me) {
          localStorage.removeItem('token');
          showLoggedOut();
          return;
        }
        showLoggedIn(me);
      })
      .catch(() => showLoggedOut());
  } else {
    showLoggedOut();
  }

  logout && logout.addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    location.href = '/';
  });

  // Theme toggle
  const themeBtn = document.getElementById('theme-toggle');
  function updateThemeIcon() {
    if (!themeBtn) return;
    const isLight = document.documentElement.dataset.theme === 'light';
    themeBtn.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    themeBtn.title = isLight ? 'Светлая тема' : 'Тёмная тема';
  }
  updateThemeIcon();
  themeBtn && themeBtn.addEventListener('click', () => {
    const cur = document.documentElement.dataset.theme;
    const next = cur === 'light' ? 'dark' : 'light';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
    updateThemeIcon();
    // Перерисовать графики если они есть
    if (location.pathname === '/profile') location.reload();
  });
})();
