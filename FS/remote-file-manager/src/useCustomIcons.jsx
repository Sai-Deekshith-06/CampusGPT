import { useEffect } from "react";

export function useCustomIcons_(authenticated, files, currentPath) {
  useEffect(() => {
    if (!authenticated) return;

    const PREVIEWABLE_EXTS = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf', 'txt', 'csv', 'json', 'md'];

    const SVGS = {
      default: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="custom-svg" style="color: #6155b4;"><path d="M14 11H8M10 15H8M16 7H8M20 12V6.8C20 5.11984 20 4.27976 19.673 3.63803C19.3854 3.07354 18.9265 2.6146 18.362 2.32698C17.7202 2 16.8802 2 15.2 2H8.8C7.11984 2 6.27976 2 5.63803 2.32698C5.07354 2.6146 4.6146 3.07354 4.32698 3.63803C4 4.27976 4 5.11984 4 6.8V17.2C4 18.8802 4 19.7202 4.32698 20.362C4.6146 20.9265 5.07354 21.3854 5.63803 21.673C6.27976 22 7.11984 22 8.8 22H12M16 16L21 21M21 16L16 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
      markdown: `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" class="custom-svg" style="width: 24px; height: 24px; color: #6155b4; fill: currentColor;"><path d="M854.6 288.7c6 6 9.4 14.1 9.4 22.6V928c0 17.7-14.3 32-32 32H192c-17.7 0-32-14.3-32-32V96c0-17.7 14.3-32 32-32h424.7c8.5 0 16.7 3.4 22.7 9.4l215.2 215.3zM790.2 326L602 137.8V326h188.2zM426.13 600.93l59.11 132.97a16 16 0 0 0 14.62 9.5h24.06a16 16 0 0 0 14.63-9.51l59.1-133.35V758a16 16 0 0 0 16.01 16H641a16 16 0 0 0 16-16V486a16 16 0 0 0-16-16h-34.75a16 16 0 0 0-14.67 9.62L512.1 662.2l-79.48-182.59a16 16 0 0 0-14.67-9.61H383a16 16 0 0 0-16 16v272a16 16 0 0 0 16 16h27.13a16 16 0 0 0 16-16V600.93z"/></svg>`
    };

    const applyIcons = () => {
      document.querySelectorAll('.hdgrfm-file-item').forEach(node => {
        const nameNode = node.querySelector('.hdgrfm-file-name');
        if (!nameNode) return; // Skip folders

        const name = nameNode.textContent || '';
        const iconContainer = node.querySelector('.hdgrfm-file-icon');
        if (!iconContainer) return;

        const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : '';
        const isPreviewable = PREVIEWABLE_EXTS.includes(ext);
        const isMarkdown = ext === 'md';

        const originalSvg = iconContainer.querySelector('svg:not(.custom-svg)');
        let customIcon = iconContainer.querySelector('.custom-file-icon');

        if (isPreviewable && !isMarkdown) {
          // SHOW original library icon
          if (originalSvg) originalSvg.style.display = '';
          if (customIcon) {
            customIcon.style.display = 'none';
            customIcon.dataset.iconType = 'none';
          }
        } else {
          // INJECT custom icon (Markdown or Default)
          if (originalSvg) originalSvg.style.display = 'none';

          if (!customIcon) {
            customIcon = document.createElement('div');
            customIcon.className = 'custom-file-icon';
            customIcon.style.display = 'flex';
            customIcon.style.alignItems = 'center';
            customIcon.style.justifyContent = 'center';
            customIcon.style.width = '100%';
            customIcon.style.height = '100%';
            iconContainer.appendChild(customIcon);
          }
          customIcon.style.display = 'flex';

          const targetType = isMarkdown ? 'markdown' : 'default';
          if (customIcon.dataset.iconType !== targetType) {
            customIcon.innerHTML = isMarkdown ? SVGS.markdown : SVGS.default;
            customIcon.dataset.iconType = targetType;
          }
        }
      });
    };

    const observer = new MutationObserver(applyIcons);
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(applyIcons, 100);

    return () => observer.disconnect();
  }, [authenticated, files, currentPath]);
}

export default function useCustomIcons(authenticated) {
  useEffect(() => {
    if (!authenticated) return;

    const markdownSvg = `
      <svg
        class="custom-svg"
        width="24"
        height="24"
        viewBox="0 0 1024 1024"
        xmlns="http://www.w3.org/2000/svg"
        style="display:block;width:24px;height:24px;fill:#6155b4;"
      >
        <path d="M854.6 288.7c6 6 9.4 14.1 9.4 22.6V928c0 17.7-14.3 32-32 32H192c-17.7 0-32-14.3-32-32V96c0-17.7 14.3-32 32-32h424.7c8.5 0 16.7 3.4 22.7 9.4l215.2 215.3zM790.2 326L602 137.8V326h188.2zM426.13 600.93l59.11 132.97a16 16 0 0 0 14.62 9.5h24.06a16 16 0 0 0 14.63-9.51l59.1-133.35V758a16 16 0 0 0 16.01 16H641a16 16 0 0 0 16-16V486a16 16 0 0 0-16-16h-34.75a16 16 0 0 0-14.67 9.62L512.1 662.2l-79.48-182.59a16 16 0 0 0-14.67-9.61H383a16 16 0 0 0-16 16v272a16 16 0 0 0 16 16h27.13a16 16 0 0 0 16-16V600.93z"/>
      </svg>
    `;

    const applyMarkdownIcons = () => {
      document
        .querySelectorAll(".hdgrfm-file-item")
        .forEach((node) => {
          const nameNode = node.querySelector(".hdgrfm-file-name");
          const iconContainer = node.querySelector(".hdgrfm-file-icon");

          if (!nameNode || !iconContainer) return;

          const name = nameNode.textContent.trim();

          // Only Markdown files are modified.
          const isMarkdown = /\\.md$/i.test(name);

          const existingCustom =
            iconContainer.querySelector(".custom-file-icon");

          if (!isMarkdown) {
            // Never touch non-Markdown files.
            if (existingCustom) {
              existingCustom.remove();
            }

            iconContainer
              .querySelectorAll("svg")
              .forEach((svg) => {
                svg.style.display = "";
              });

            return;
          }

          // Hide only the library icon for Markdown.
          iconContainer
            .querySelectorAll("svg:not(.custom-svg)")
            .forEach((svg) => {
              svg.style.display = "none";
            });

          // Don't create it again if already present.
          if (existingCustom) return;

          const customIcon = document.createElement("div");

          customIcon.className = "custom-file-icon";

          Object.assign(customIcon.style, {
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            height: "100%",
          });

          customIcon.innerHTML = markdownSvg;

          iconContainer.appendChild(customIcon);
        });
    };

    // Initial render
    applyMarkdownIcons();

    // Watch for FileManager rendering new rows
    const observer = new MutationObserver(() => {
      applyMarkdownIcons();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => observer.disconnect();
  }, [authenticated]);
}
