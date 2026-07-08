export function scrollToVerifyWorkspace(): void {
  window.requestAnimationFrame(() => {
    const target = document.getElementById("verify-workspace");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}
