// Floating animation for game cards
document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".game-card");

  cards.forEach((card, index) => {
    card.style.animation = `float 3s ease-in-out ${
      index * 0.2
    }s infinite alternate`;
  });

  // Add particle background (updated for black theme)
  const canvas = document.createElement("canvas");
  document.querySelector(".background-animation").appendChild(canvas);
  canvas.style.position = "absolute";
  canvas.style.width = "100%";
  canvas.style.height = "100%";

  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  // Particles with white/gray colors for black theme
  const particles = [];
  for (let i = 0; i < 50; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 3 + 1,
      speedX: Math.random() * 1 - 0.5,
      speedY: Math.random() * 1 - 0.5,
      color: `rgba(255, 255, 255, ${Math.random() * 0.3 + 0.1})`, // White/gray particles
    });
  }

  function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach((particle) => {
      ctx.fillStyle = particle.color;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fill();

      particle.x += particle.speedX;
      particle.y += particle.speedY;

      // Bounce off edges
      if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1;
      if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1;
    });

    requestAnimationFrame(animateParticles);
  }

  animateParticles();

  // Handle window resize
  window.addEventListener("resize", () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });
});
