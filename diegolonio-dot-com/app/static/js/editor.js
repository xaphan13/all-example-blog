// Editor markdown del admin: un solo panel con toggle Edit/Preview
// + subida de imágenes.
//
// - Preview: al pulsar el tab "Preview" se manda el markdown a
//   POST /admin/api/preview, que responde el HTML renderizado con el mismo
//   pipeline que al guardar; KaTeX renderiza la math encima. El tab "Edit"
//   vuelve al textarea.
// - Imágenes: arrastrar (o pegar) una imagen la sube a POST /admin/api/images
//   y en el texto solo se inserta el link markdown ![alt](url); al pasar a
//   Preview se ve como quedará publicada.

const textarea = document.getElementById("content_md");
const preview = document.getElementById("preview");
const tabEdit = document.getElementById("tab-edit");
const tabPreview = document.getElementById("tab-preview");

const KATEX_DELIMITERS = [
    { left: "$$", right: "$$", display: true },
    { left: "$", right: "$", display: false },
    { left: "\\(", right: "\\)", display: false },
    { left: "\\[", right: "\\]", display: true },
];

// --- Toggle Edit / Preview ---------------------------------------------------

async function showPreview() {
    const response = await fetch("/admin/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content_md: textarea.value }),
    });
    if (!response.ok) return;

    preview.innerHTML = (await response.json()).html;

    // KaTeX se carga con defer; si aún no está listo, no pasa nada
    if (window.renderMathInElement) {
        renderMathInElement(preview, {
            delimiters: KATEX_DELIMITERS,
            throwOnError: false,
        });
    }

    textarea.hidden = true;
    preview.hidden = false;
    tabPreview.classList.add("active");
    tabEdit.classList.remove("active");
}

function showEdit() {
    preview.hidden = true;
    textarea.hidden = false;
    tabEdit.classList.add("active");
    tabPreview.classList.remove("active");
    textarea.focus();
}

tabPreview.addEventListener("click", showPreview);
tabEdit.addEventListener("click", showEdit);

// --- Subida de imágenes (drag & drop y pegar) --------------------------------

async function uploadImage(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/admin/api/images", {
        method: "POST",
        body: formData,
    });
    if (!response.ok) {
        alert(`Could not upload "${file.name}"`);
        return null;
    }
    return (await response.json()).url;
}

function insertAtCursor(text) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    textarea.value = textarea.value.slice(0, start) + text + textarea.value.slice(end);
    textarea.selectionStart = textarea.selectionEnd = start + text.length;
    textarea.focus();
}

async function handleImageFiles(files) {
    for (const file of files) {
        if (!file.type.startsWith("image/")) continue;
        const url = await uploadImage(file);
        if (url) {
            const alt = file.name.replace(/\.[^.]+$/, "");
            insertAtCursor(`![${alt}](${url})\n`);
        }
    }
}

textarea.addEventListener("dragover", (event) => {
    event.preventDefault(); // necesario para permitir el drop
    textarea.classList.add("dragging");
});

textarea.addEventListener("dragleave", () => {
    textarea.classList.remove("dragging");
});

textarea.addEventListener("drop", (event) => {
    event.preventDefault();
    textarea.classList.remove("dragging");
    handleImageFiles(event.dataTransfer.files);
});

textarea.addEventListener("paste", (event) => {
    const files = [...event.clipboardData.files];
    if (files.length > 0) {
        event.preventDefault();
        handleImageFiles(files);
    }
});

// --- Imagen de portada --------------------------------------------------------
// El input de texto es la fuente de verdad (es lo que viaja en el form).
// Con cover puesta, el input se oculta y se muestra un chip con el nombre
// del archivo: su × la quita, y al pasar el mouse aparece el preview
// flotante (el hover lo maneja CSS; aquí solo se pone el src).

const coverInput = document.getElementById("cover_image");
const coverChip = document.getElementById("cover-chip");
const coverName = document.getElementById("cover-name");
const coverChoose = document.getElementById("cover-choose");
const coverClear = document.getElementById("cover-clear");
const coverFile = document.getElementById("cover-file");
const coverPopoverImg = document.getElementById("cover-popover-img");

function setCover(url) {
    coverInput.value = url;
    coverInput.hidden = Boolean(url); // oculto sigue enviándose en el form
    coverChip.hidden = !url;
    if (url) {
        // Última parte de la URL como nombre visible: /media/abc.png → abc.png
        coverName.textContent = url.split("/").pop() || url;
        coverName.title = url; // la URL completa, como tooltip nativo
        coverPopoverImg.src = url;
    } else {
        coverPopoverImg.removeAttribute("src"); // src="" haría un request a la página
    }
}

async function uploadCover(files) {
    const file = [...files].find((f) => f.type.startsWith("image/"));
    if (!file) return;
    const url = await uploadImage(file);
    if (url) setCover(url);
}

coverChoose.addEventListener("click", () => coverFile.click());

coverFile.addEventListener("change", () => {
    uploadCover(coverFile.files);
    coverFile.value = ""; // permite volver a elegir el mismo archivo
});

coverClear.addEventListener("click", () => {
    setCover("");
    coverInput.focus();
});

// Escribir/pegar una URL a mano también se convierte en chip (al salir del campo)
coverInput.addEventListener("change", () => setCover(coverInput.value.trim()));

coverInput.addEventListener("dragover", (event) => {
    event.preventDefault();
    coverInput.classList.add("dragging");
});

coverInput.addEventListener("dragleave", () => {
    coverInput.classList.remove("dragging");
});

coverInput.addEventListener("drop", (event) => {
    event.preventDefault();
    coverInput.classList.remove("dragging");
    uploadCover(event.dataTransfer.files);
});

// Estado inicial: al editar un post que ya tiene cover, mostrar el chip
setCover(coverInput.value.trim());

// --- Summary autoajustable ------------------------------------------------------
// El summary no se redimensiona a mano (resize: none en CSS): su altura
// sigue al texto, creciendo y encogiendo mientras se escribe.

const summary = document.getElementById("summary");

function resizeSummary() {
    summary.style.height = "auto"; // resetea para poder encoger al borrar
    summary.style.height = `${summary.scrollHeight + 2}px`; // +2: el borde (1px por lado)
}

summary.addEventListener("input", resizeSummary);
resizeSummary(); // estado inicial: al editar un post con summary de varias líneas

// --- Tags como chips ----------------------------------------------------------
// El input oculto #tags es la fuente de verdad (viaja en el form como
// "ml, python"). Los chips y el input de escritura son solo interfaz:
// una coma o Enter convierte lo escrito en chip (en minúsculas) y la ×
// de cada chip lo elimina.

const tagsHidden = document.getElementById("tags");
const tagsField = document.getElementById("tags-field");
const tagsEntry = document.getElementById("tags-entry");

let tagList = [];

function renderTags() {
    tagsField.querySelectorAll(".tag-chip").forEach((chip) => chip.remove());

    for (const tag of tagList) {
        const chip = document.createElement("span");
        chip.className = "tag-chip";
        chip.textContent = tag;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.setAttribute("aria-label", `Remove tag ${tag}`);
        remove.textContent = "×";
        remove.addEventListener("click", () => {
            tagList = tagList.filter((t) => t !== tag);
            renderTags();
        });

        chip.appendChild(remove);
        tagsField.insertBefore(chip, tagsEntry);
    }

    tagsHidden.value = tagList.join(", ");
}

function addTags(text) {
    // split(",") también cubre pegar "a, b, c" de golpe
    for (const part of text.split(",")) {
        const tag = part.trim().toLowerCase();
        if (tag && !tagList.includes(tag)) tagList.push(tag);
    }
    renderTags();
    // Al agregar escribiendo, desplaza el scroll para que el input siga a la
    // vista; en la carga inicial no, para que se vean los primeros tags
    if (document.activeElement === tagsEntry) {
        tagsField.scrollLeft = tagsField.scrollWidth;
    }
}

// Al teclear una coma, lo escrito hasta ahí se convierte en chip
tagsEntry.addEventListener("input", () => {
    if (tagsEntry.value.includes(",")) {
        addTags(tagsEntry.value);
        tagsEntry.value = "";
    }
});

tagsEntry.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault(); // que Enter agregue el tag, no envíe el form
        addTags(tagsEntry.value);
        tagsEntry.value = "";
    } else if (event.key === "Backspace" && tagsEntry.value === "") {
        tagList.pop(); // Backspace con el campo vacío quita el último chip
        renderTags();
    }
});

// Lo escrito sin coma no se pierde: se convierte en chip al salir del campo
// (el blur ocurre antes del submit, así que Save tampoco lo pierde)
tagsEntry.addEventListener("blur", () => {
    addTags(tagsEntry.value);
    tagsEntry.value = "";
});

// Clic en el "marco" enfoca el input, como si todo fuera un solo campo
tagsField.addEventListener("click", (event) => {
    if (event.target === tagsField) tagsEntry.focus();
});

// Estado inicial: al editar un post, sus tags ya vienen en el input oculto
addTags(tagsHidden.value);
