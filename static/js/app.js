/**
 * UniVault: College Notes and University Exam Material Sharing Portal
 * Interactive Frontend Controller (Vanilla ES6+ with Reactive Architecture)
 */

(function () {
    "use strict";

    // Application State
    const state = {
        search: "",
        branch: "all",
        semester: "all",
        university: "all",
        materialType: "all",
        sortBy: "popular",
        page: 1,
        perPage: 12,
        totalPages: 1,
        totalItems: 0,
        materials: [],
        bookmarks: [],
        upvotedIds: [],
        currentPreviewItem: null,
        selectedRating: 0,
        viewMode: localStorage.getItem("univault_view_mode") === "list" ? "list" : "grid"
    };

    // DOM Elements
    const elements = {
        themeToggle: document.getElementById("themeToggle"),
        themeIcon: document.getElementById("themeIcon"),
        searchInput: document.getElementById("searchInput"),
        clearSearchBtn: document.getElementById("clearSearchBtn"),
        branchFilter: document.getElementById("branchFilter"),
        semesterFilter: document.getElementById("semesterFilter"),
        universityFilter: document.getElementById("universityFilter"),
        materialTypeFilter: document.getElementById("materialTypeFilter"),
        sortByFilter: document.getElementById("sortByFilter"),
        materialsGrid: document.getElementById("materialsGrid"),
        materialsCount: document.getElementById("materialsCount"),
        loadingSkeleton: document.getElementById("loadingSkeleton"),
        emptyState: document.getElementById("emptyState"),
        paginationContainer: document.getElementById("paginationContainer"),
        prevPageBtn: document.getElementById("prevPageBtn"),
        nextPageBtn: document.getElementById("nextPageBtn"),
        pageInfo: document.getElementById("pageInfo"),

        // Preview Modal
        previewModal: document.getElementById("previewModal"),
        closePreviewBtn: document.getElementById("closePreviewBtn"),
        previewTitle: document.getElementById("previewTitle"),
        previewBadge: document.getElementById("previewBadge"),
        previewCode: document.getElementById("previewCode"),
        previewUniversity: document.getElementById("previewUniversity"),
        previewSemester: document.getElementById("previewSemester"),
        previewBranch: document.getElementById("previewBranch"),
        previewAuthor: document.getElementById("previewAuthor"),
        previewPages: document.getElementById("previewPages"),
        previewSize: document.getElementById("previewSize"),
        previewRating: document.getElementById("previewRating"),
        previewDownloads: document.getElementById("previewDownloads"),
        previewDescription: document.getElementById("previewDescription"),
        previewTags: document.getElementById("previewTags"),
        previewContent: document.getElementById("previewContent"),
        previewDownloadBtn: document.getElementById("previewDownloadBtn"),
        previewBookmarkBtn: document.getElementById("previewBookmarkBtn"),
        reviewsList: document.getElementById("reviewsList"),
        reviewForm: document.getElementById("reviewForm"),
        starButtons: document.querySelectorAll(".star-btn"),

        // Upload Modal
        uploadModal: document.getElementById("uploadModal"),
        openUploadBtn: document.getElementById("openUploadBtn"),
        heroUploadBtn: document.getElementById("heroUploadBtn"),
        closeUploadBtn: document.getElementById("closeUploadBtn"),
        uploadForm: document.getElementById("uploadForm"),
        fileDropZone: document.getElementById("fileDropZone"),
        fileInput: document.getElementById("fileInput"),
        selectedFileName: document.getElementById("selectedFileName"),
        uploadSubmitBtn: document.getElementById("uploadSubmitBtn"),

        // Study Kit Drawer
        studyKitDrawer: document.getElementById("studyKitDrawer"),
        openStudyKitBtn: document.getElementById("openStudyKitBtn"),
        closeStudyKitBtn: document.getElementById("closeStudyKitBtn"),
        studyKitCountBadge: document.getElementById("studyKitCountBadge"),
        studyKitItems: document.getElementById("studyKitItems"),
        studyKitEmpty: document.getElementById("studyKitEmpty"),
        clearStudyKitBtn: document.getElementById("clearStudyKitBtn"),
        gridViewBtn: document.getElementById("gridViewBtn"),
        listViewBtn: document.getElementById("listViewBtn"),
        sectionUploadBtn: document.getElementById("sectionUploadBtn"),

        // Toast Container
        toastContainer: document.getElementById("toastContainer")
    };

    // Category styling mapping
    const categoryClasses = {
        "Lecture Notes": "badge-lecture-notes",
        "Previous Year Questions (PYQs)": "badge-pyqs",
        "Formula Sheets / Cheat Sheets": "badge-formula-sheets",
        "Lab Manuals": "badge-lab-manuals",
        "Solved Papers": "badge-solved-papers",
        "Syllabus": "badge-syllabus"
    };

    // -------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------
    function init() {
        initTheme();
        bindEvents();
        setViewMode(state.viewMode);
        initScrollReveals();
        loadAccountState().finally(() => {
            updateStudyKitCount();
            fetchMaterials();
        });
    }

    function csrfHeaders(extra = {}) {
        return { ...extra, "X-CSRF-Token": window.UNIVAULT_CSRF || document.querySelector('meta[name="csrf-token"]')?.content || "" };
    }

    async function loadAccountState() {
        if (!window.UNIVAULT_AUTHENTICATED) return;
        try {
            const response = await fetch("/api/user-state");
            if (!response.ok) return;
            const data = await response.json();
            state.bookmarks = data.bookmarks || [];
            state.upvotedIds = data.upvoted_ids || [];
        } catch (error) { console.error("Unable to load saved materials.", error); }
    }

    // -------------------------------------------------------------
    // Theme Manager
    // -------------------------------------------------------------
    function initTheme() {
        const savedTheme = localStorage.getItem("univault_theme");
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        
        if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
            document.documentElement.classList.add("dark");
            updateThemeIcon(true);
        } else {
            document.documentElement.classList.remove("dark");
            updateThemeIcon(false);
        }

        if (elements.themeToggle) {
            elements.themeToggle.addEventListener("click", () => {
                const isDark = document.documentElement.classList.toggle("dark");
                localStorage.setItem("univault_theme", isDark ? "dark" : "light");
                updateThemeIcon(isDark);
            });
        }
    }

    function updateThemeIcon(isDark) {
        if (!elements.themeIcon) return;
        const actionLabel = isDark ? "Switch to light mode" : "Switch to dark mode";
        if (isDark) {
            elements.themeIcon.setAttribute("data-lucide", "sun");
        } else {
            elements.themeIcon.setAttribute("data-lucide", "moon");
        }
        elements.themeToggle?.setAttribute("aria-label", actionLabel);
        elements.themeToggle?.setAttribute("title", actionLabel);
        if (window.lucide) window.lucide.createIcons();
    }

    // -------------------------------------------------------------
    // Event Listeners
    // -------------------------------------------------------------
    function bindEvents() {
        // Debounced search
        let debounceTimer;
        elements.searchInput?.addEventListener("input", (e) => {
            state.search = e.target.value;
            elements.clearSearchBtn?.classList.toggle("hidden", !state.search);
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                state.page = 1;
                fetchMaterials();
            }, 300);
        });

        elements.clearSearchBtn?.addEventListener("click", () => {
            if (elements.searchInput) elements.searchInput.value = "";
            state.search = "";
            elements.clearSearchBtn.classList.add("hidden");
            state.page = 1;
            fetchMaterials();
        });

        elements.gridViewBtn?.addEventListener("click", () => setViewMode("grid"));
        elements.listViewBtn?.addEventListener("click", () => setViewMode("list"));
        elements.sectionUploadBtn?.addEventListener("click", openUploadModal);
        document.addEventListener("keydown", (event) => {
            const target = event.target;
            const editing = target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));
            if (event.key === "/" && !editing && elements.searchInput) {
                event.preventDefault();
                elements.searchInput.focus();
            }
        });

        // Filters change
        const filterElements = [
            { el: elements.branchFilter, key: "branch" },
            { el: elements.semesterFilter, key: "semester" },
            { el: elements.universityFilter, key: "university" },
            { el: elements.materialTypeFilter, key: "materialType" },
            { el: elements.sortByFilter, key: "sortBy" }
        ];

        filterElements.forEach(({ el, key }) => {
            el?.addEventListener("change", (e) => {
                state[key] = e.target.value;
                state.page = 1;
                fetchMaterials();
            });
        });

        // Quick Topic Chips (Hero Section)
        document.querySelectorAll(".quick-chip").forEach((btn) => {
            btn.addEventListener("click", () => {
                const filterType = btn.getAttribute("data-filter-type");
                const filterValue = btn.getAttribute("data-filter-value");

                if (filterType === "search") {
                    if (elements.searchInput) elements.searchInput.value = filterValue;
                    state.search = filterValue;
                    elements.clearSearchBtn?.classList.remove("hidden");
                } else if (filterType === "material_type") {
                    if (elements.materialTypeFilter) elements.materialTypeFilter.value = filterValue;
                    state.materialType = filterValue;
                } else if (filterType === "semester") {
                    if (elements.semesterFilter) elements.semesterFilter.value = filterValue;
                    state.semester = filterValue;
                }
                
                state.page = 1;
                fetchMaterials();
                document.getElementById("materialsSection")?.scrollIntoView({ behavior: "smooth" });
            });
        });

        // Pagination
        elements.prevPageBtn?.addEventListener("click", () => {
            if (state.page > 1) {
                state.page--;
                fetchMaterials();
                scrollToTop();
            }
        });

        elements.nextPageBtn?.addEventListener("click", () => {
            if (state.page < state.totalPages) {
                state.page++;
                fetchMaterials();
                scrollToTop();
            }
        });

        // Modals
        elements.closePreviewBtn?.addEventListener("click", closePreviewModal);
        elements.previewModal?.addEventListener("click", (e) => {
            if (e.target === elements.previewModal) closePreviewModal();
        });

        elements.openUploadBtn?.addEventListener("click", openUploadModal);
        elements.heroUploadBtn?.addEventListener("click", openUploadModal);
        elements.closeUploadBtn?.addEventListener("click", closeUploadModal);
        elements.uploadModal?.addEventListener("click", (e) => {
            if (e.target === elements.uploadModal) closeUploadModal();
        });

        // File Drag & Drop
        if (elements.fileDropZone && elements.fileInput) {
            elements.fileDropZone.addEventListener("click", () => elements.fileInput.click());
            elements.fileDropZone.addEventListener("dragover", (e) => {
                e.preventDefault();
                elements.fileDropZone.classList.add("border-indigo-500", "bg-indigo-50/50", "dark:bg-indigo-950/20");
            });
            elements.fileDropZone.addEventListener("dragleave", () => {
                elements.fileDropZone.classList.remove("border-indigo-500", "bg-indigo-50/50", "dark:bg-indigo-950/20");
            });
            elements.fileDropZone.addEventListener("drop", (e) => {
                e.preventDefault();
                elements.fileDropZone.classList.remove("border-indigo-500", "bg-indigo-50/50", "dark:bg-indigo-950/20");
                if (e.dataTransfer.files.length) {
                    elements.fileInput.files = e.dataTransfer.files;
                    handleFileSelect(e.dataTransfer.files[0]);
                }
            });
            elements.fileInput.addEventListener("change", (e) => {
                if (e.target.files.length) handleFileSelect(e.target.files[0]);
            });
        }

        // Upload Form Submission
        elements.uploadForm?.addEventListener("submit", handleUploadSubmit);

        // Review Form Star Buttons
        elements.starButtons?.forEach((btn) => {
            btn.addEventListener("click", () => {
                const rating = parseInt(btn.getAttribute("data-star"), 10);
                setReviewRating(rating);
            });
        });

        // Review Submission
        elements.reviewForm?.addEventListener("submit", handleReviewSubmit);

        // Study Kit Drawer
        elements.openStudyKitBtn?.addEventListener("click", openStudyKit);
        elements.closeStudyKitBtn?.addEventListener("click", closeStudyKit);
        elements.clearStudyKitBtn?.addEventListener("click", clearStudyKit);

        // Escape Key for Modals
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                closePreviewModal();
                closeUploadModal();
                closeStudyKit();
            }
        });
    }

    function scrollToTop() {
        document.getElementById("materialsSection")?.scrollIntoView({ behavior: "smooth" });
    }

    function setViewMode(mode) {
        state.viewMode = mode === "list" ? "list" : "grid";
        localStorage.setItem("univault_view_mode", state.viewMode);
        elements.materialsGrid?.classList.toggle("materials-list-view", state.viewMode === "list");
        elements.gridViewBtn?.setAttribute("aria-pressed", String(state.viewMode === "grid"));
        elements.listViewBtn?.setAttribute("aria-pressed", String(state.viewMode === "list"));
    }

    function initScrollReveals() {
        const targets = document.querySelectorAll("#collectionsSection, #materialsSection, #leaderboardSection");
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
        targets.forEach((target) => target.classList.add("reveal-on-scroll"));
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.08 });
        targets.forEach((target) => observer.observe(target));
    }

    function handleFileSelect(file) {
        if (!elements.selectedFileName) return;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        elements.selectedFileName.textContent = `Selected: ${file.name} (${sizeMb} MB)`;
        elements.selectedFileName.classList.remove("hidden");
    }

    // -------------------------------------------------------------
    // Fetch & Render Materials
    // -------------------------------------------------------------
    async function fetchMaterials() {
        showLoading(true);

        const params = new URLSearchParams({
            search: state.search,
            branch: state.branch,
            semester: state.semester,
            university: state.university,
            material_type: state.materialType,
            sort_by: state.sortBy,
            page: state.page,
            per_page: state.perPage
        });

        try {
            const res = await fetch(`/api/materials?${params.toString()}`);
            if (!res.ok) throw new Error("Failed to load materials");
            const data = await res.json();

            state.materials = data.materials || [];
            state.totalItems = data.total || 0;
            state.totalPages = data.total_pages || 1;

            renderMaterialsList(state.materials);
            updatePaginationUI();
        } catch (error) {
            console.error("Error fetching materials:", error);
            showToast("Materials could not be loaded. Please check your connection and try again.", "error");
        } finally {
            showLoading(false);
        }
    }

    function showLoading(isLoading) {
        if (elements.loadingSkeleton) {
            elements.loadingSkeleton.classList.toggle("hidden", !isLoading);
        }
        if (elements.materialsGrid && isLoading) {
            elements.materialsGrid.classList.add("hidden");
        }
    }

    function renderMaterialsList(materials) {
        if (!elements.materialsGrid) return;

        if (elements.materialsCount) {
            elements.materialsCount.textContent = `${state.totalItems} material${state.totalItems === 1 ? '' : 's'} found`;
        }

        if (materials.length === 0) {
            elements.materialsGrid.classList.add("hidden");
            elements.emptyState?.classList.remove("hidden");
            return;
        }

        elements.emptyState?.classList.add("hidden");
        elements.materialsGrid.classList.remove("hidden");
        elements.materialsGrid.innerHTML = "";

        materials.forEach((item) => {
            const card = createMaterialCard(item);
            elements.materialsGrid.appendChild(card);
        });

        if (window.lucide) window.lucide.createIcons();
    }

   function createMaterialCard(item) {
    const isUpvoted = state.upvotedIds.includes(item.id);
    const isBookmarked = state.bookmarks.some((b) => b.id === item.id);

    const badgeColor =
        categoryClasses[item.material_type] ||
        "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200";

    const uploaderName = item.uploader_name || "UniVault Contributor";

    // Profile photo supplied by the backend.
    const uploaderAvatar = item.uploader_avatar || "";

    const avatarHtml = uploaderAvatar
        ? `
            <img
                src="${escapeHtml(uploaderAvatar)}"
                alt="${escapeHtml(uploaderName)}"
                class="w-8 h-8 rounded-full object-cover border border-slate-200 dark:border-slate-700 shadow-sm flex-shrink-0"
                loading="lazy"
                onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
            >
            <span
                class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 flex items-center justify-center text-xs font-bold border border-indigo-200 dark:border-indigo-800"
                style="display:none;"
                aria-hidden="true"
            >
                ${escapeHtml(uploaderName.charAt(0).toUpperCase())}
            </span>
        `
        : `
            <span
                class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 flex items-center justify-center text-xs font-bold border border-indigo-200 dark:border-indigo-800 flex-shrink-0"
                aria-hidden="true"
            >
                ${escapeHtml(uploaderName.charAt(0).toUpperCase())}
            </span>
        `;

    const card = document.createElement("div");

    card.className =
        "material-card glass-panel rounded-2xl p-5 flex flex-col justify-between card-hover-glow transition-all duration-300 relative group";

    card.innerHTML = `
        <div>

            <!-- Top Tags & Bookmark Row -->
            <div class="flex items-center justify-between gap-2 mb-3">

                <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${badgeColor}">
                    ${escapeHtml(item.material_type)}
                </span>

                ${
                    window.UNIVAULT_AUTHENTICATED
                        ? `
                    <button
                        class="bookmark-btn p-1.5 rounded-lg text-slate-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors"
                        data-id="${item.id}"
                        title="${isBookmarked ? "Remove from Exam Kit" : "Save to Exam Kit"}"
                        aria-label="${isBookmarked ? "Remove from Exam Kit" : "Save to Exam Kit"}"
                    >
                        <i
                            data-lucide="bookmark"
                            class="w-4 h-4 ${isBookmarked ? "fill-amber-500 text-amber-500" : ""}"
                        ></i>
                    </button>
                    `
                        : ""
                }

            </div>

            <!-- Subject & Code Badges -->
            <div class="flex flex-wrap items-center gap-1.5 mb-2 text-xs text-slate-500 dark:text-slate-400">

                <span class="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-700 dark:text-slate-300 font-medium">
                    ${escapeHtml(item.subject_code || "COURSE")}
                </span>

                <span>•</span>

                <span class="font-medium text-slate-600 dark:text-slate-300">
                    ${escapeHtml(item.semester)}
                </span>

                <span>•</span>

                <span>
                    ${escapeHtml(item.academic_year || "2024")}
                </span>

            </div>

            <!-- Title -->
            <h3
                class="font-bold text-slate-900 dark:text-white text-base leading-snug mb-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 cursor-pointer preview-trigger"
                data-id="${item.id}"
            >
                ${escapeHtml(item.title)}
            </h3>

            <!-- University & Branch -->
            <div class="flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 font-medium mb-3">

                <i
                    data-lucide="building-2"
                    class="w-3.5 h-3.5 flex-shrink-0"
                ></i>

                <span class="truncate">
                    ${escapeHtml(item.university)}
                </span>

            </div>

            <!-- Description -->
            <p
                class="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 mb-4 leading-relaxed"
            >
                ${escapeHtml(
                    item.description ||
                    item.preview_content ||
                    "Comprehensive study resource and revision reference."
                )}
            </p>

            <!-- Uploader Profile -->
            <div class="flex items-center gap-2.5 mb-4">

                ${avatarHtml}

                <div class="min-w-0">

                    <p class="text-[10px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500">
                        Shared by
                    </p>

                    <p class="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate">
                        ${escapeHtml(uploaderName)}
                    </p>

                </div>

            </div>

        </div>

        <!-- Footer Details & Actions -->
        <div class="pt-3 border-t border-slate-100 dark:border-slate-800/80">

            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-3">

                <!-- Rating & Reviews -->
                <div class="flex items-center gap-1">

                    <i
                        data-lucide="star"
                        class="w-3.5 h-3.5 fill-amber-400 text-amber-400"
                    ></i>

                    <span class="font-bold text-slate-700 dark:text-slate-200">
                        ${item.avg_rating || "5.0"}
                    </span>

                    <span>
                        (${item.review_count || 0})
                    </span>

                </div>

                <!-- Downloads & Size -->
                <div class="flex items-center gap-2">

                    <span
                        class="flex items-center gap-1"
                        title="Downloads"
                    >

                        <i
                            data-lucide="download"
                            class="w-3.5 h-3.5 text-slate-400"
                        ></i>

                        ${formatNumber(item.downloads_count)}

                    </span>

                    <span>•</span>

                    <span>
                        ${item.page_count || 24} pgs
                    </span>

                </div>

            </div>

            <!-- Card Action Buttons -->
            <div class="grid grid-cols-5 gap-2">

                ${
                    window.UNIVAULT_AUTHENTICATED
                        ? `
                    <button
                        class="upvote-btn col-span-2 flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-rose-400 dark:hover:border-rose-500 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 transition-all ${
                            isUpvoted
                                ? "bg-rose-50 dark:bg-rose-950/40 border-rose-300 text-rose-600 dark:text-rose-400"
                                : "bg-white/50 dark:bg-slate-800/50"
                        }"
                        data-id="${item.id}"
                    >

                        <i
                            data-lucide="heart"
                            class="w-3.5 h-3.5 ${
                                isUpvoted
                                    ? "fill-rose-500 text-rose-500"
                                    : ""
                            }"
                        ></i>

                        <span class="upvote-count">
                            ${item.upvotes_count}
                        </span>

                    </button>
                    `
                        : `
                    <span class="col-span-2 flex items-center justify-center gap-1.5 py-2 text-xs text-slate-500">

                        <i
                            data-lucide="heart"
                            class="h-3.5 w-3.5"
                        ></i>

                        ${item.upvotes_count}

                    </span>
                    `
                }

                <button
                    class="preview-btn col-span-3 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-all shadow-sm shadow-indigo-600/20 active:scale-95"
                    data-id="${item.id}"
                >

                    <i
                        data-lucide="eye"
                        class="w-3.5 h-3.5"
                    ></i>

                    <span>Preview</span>

                </button>

            </div>

        </div>
    `;

    // ---------------------------------------------------------
    // Card button events
    // ---------------------------------------------------------

    card.querySelectorAll(
        ".preview-trigger, .preview-btn"
    ).forEach((el) => {
        el.addEventListener("click", () => {
            openPreviewModal(item.id);
        });
    });

    card.querySelector(".upvote-btn")?.addEventListener(
        "click",
        () => {
            if (!window.UNIVAULT_AUTHENTICATED) {
                window.location.href = "/login";
                return;
            }

            handleUpvote(item.id, card);
        }
    );

    card.querySelector(".bookmark-btn")?.addEventListener(
        "click",
        () => {
            handleBookmarkToggle(item, card);
        }
    );

    return card;
}

    function updatePaginationUI() {
        if (!elements.paginationContainer) return;

        if (state.totalPages <= 1) {
            elements.paginationContainer.classList.add("hidden");
            return;
        }

        elements.paginationContainer.classList.remove("hidden");
        if (elements.pageInfo) {
            elements.pageInfo.textContent = `Page ${state.page} of ${state.totalPages}`;
        }

        if (elements.prevPageBtn) {
            elements.prevPageBtn.disabled = state.page <= 1;
            elements.prevPageBtn.classList.toggle("opacity-50", state.page <= 1);
            elements.prevPageBtn.classList.toggle("cursor-not-allowed", state.page <= 1);
        }

        if (elements.nextPageBtn) {
            elements.nextPageBtn.disabled = state.page >= state.totalPages;
            elements.nextPageBtn.classList.toggle("opacity-50", state.page >= state.totalPages);
            elements.nextPageBtn.classList.toggle("cursor-not-allowed", state.page >= state.totalPages);
        }
    }

    // -------------------------------------------------------------
    // Upvote Interaction
    // -------------------------------------------------------------
    async function handleUpvote(id, cardElement) {
        if (state.upvotedIds.includes(id)) {
            showToast("You have already upvoted this resource.", "info");
            return;
        }

        try {
            const res = await fetch(`/api/materials/${id}/upvote`, { method: "POST", headers: csrfHeaders() });
            const data = await res.json();

            if (data.success) {
                state.upvotedIds.push(id);

                const upvoteBtn = cardElement.querySelector(".upvote-btn");
                const countEl = cardElement.querySelector(".upvote-count");
                const heartIcon = upvoteBtn?.querySelector("i");

                if (countEl) countEl.textContent = data.upvotes_count;
                if (upvoteBtn) {
                    upvoteBtn.classList.add("bg-rose-50", "dark:bg-rose-950/40", "border-rose-300", "text-rose-600", "dark:text-rose-400");
                }
                if (heartIcon) {
                    heartIcon.classList.add("fill-rose-500", "text-rose-500", "animate-heart-pop");
                }

                showToast("Your upvote has been recorded.", "success");
            }
        } catch (error) {
            console.error("Upvote failed:", error);
            showToast("Failed to record upvote.", "error");
        }
    }

    // -------------------------------------------------------------
    // Bookmarking & Study Kit Management
    // -------------------------------------------------------------
    async function handleBookmarkToggle(item, cardElement) {
        if (!window.UNIVAULT_AUTHENTICATED) { window.location.href = "/login"; return; }
        const index = state.bookmarks.findIndex((b) => b.id === item.id);
        const bookmarkBtn = cardElement?.querySelector(".bookmark-btn");
        const icon = bookmarkBtn?.querySelector("i");

        if (index > -1) {
            const response = await fetch(`/api/bookmarks/${item.id}`, { method: "DELETE", headers: csrfHeaders() });
            if (!response.ok) { showToast("Your Study Kit could not be updated. Please try again.", "error"); return; }
            state.bookmarks.splice(index, 1);
            showToast("The resource has been removed from your Study Kit.", "info");
            if (icon) {
                icon.classList.remove("fill-amber-500", "text-amber-500");
            }
        } else {
            const response = await fetch(`/api/bookmarks/${item.id}`, { method: "POST", headers: csrfHeaders() });
            if (!response.ok) { showToast("Your Study Kit could not be updated. Please try again.", "error"); return; }
            state.bookmarks.push({
                id: item.id,
                title: item.title,
                subject_name: item.subject_name,
                subject_code: item.subject_code,
                material_type: item.material_type,
                file_url: item.file_url,
                university: item.university
            });
            showToast("The resource has been added to your Study Kit.", "success");
            if (icon) {
                icon.classList.add("fill-amber-500", "text-amber-500");
            }
        }

        updateStudyKitCount();
        renderStudyKit();
    }

    function updateStudyKitCount() {
        if (elements.studyKitCountBadge) {
            const count = state.bookmarks.length;
            elements.studyKitCountBadge.textContent = count;
            elements.studyKitCountBadge.classList.toggle("hidden", count === 0);
        }
    }

    function openStudyKit() {
        renderStudyKit();
        elements.studyKitDrawer?.classList.remove("translate-x-full");
    }

    function closeStudyKit() {
        elements.studyKitDrawer?.classList.add("translate-x-full");
    }

    async function clearStudyKit() {
        if (state.bookmarks.length === 0) return;
        const current = [...state.bookmarks];
        state.bookmarks = [];
        await Promise.all(current.map((item) => fetch(`/api/bookmarks/${item.id}`, { method: "DELETE", headers: csrfHeaders() })));
        updateStudyKitCount();
        renderStudyKit();
        fetchMaterials();
        showToast("Your Study Kit has been cleared.", "info");
    }

    function renderStudyKit() {
        if (!elements.studyKitItems) return;

        if (state.bookmarks.length === 0) {
            elements.studyKitItems.innerHTML = "";
            elements.studyKitEmpty?.classList.remove("hidden");
            return;
        }

        elements.studyKitEmpty?.classList.add("hidden");
        elements.studyKitItems.innerHTML = "";

        state.bookmarks.forEach((item) => {
            const div = document.createElement("div");
            div.className = "p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-800/40 flex items-start justify-between gap-3";

            div.innerHTML = `
                <div class="flex-1 min-w-0">
                    <span class="text-[10px] font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                        ${escapeHtml(item.material_type)}
                    </span>
                    <h4 class="font-bold text-sm text-slate-900 dark:text-white truncate cursor-pointer hover:text-indigo-600 transition-colors" data-id="${item.id}">
                        ${escapeHtml(item.title)}
                    </h4>
                    <p class="text-xs text-slate-500 dark:text-slate-400 truncate">
                        ${escapeHtml(item.subject_name)} • ${escapeHtml(item.university)}
                    </p>
                    <div class="flex items-center gap-2 mt-2">
                        <button class="kit-preview-btn text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1" data-id="${item.id}">
                            <i data-lucide="eye" class="w-3 h-3"></i> View
                        </button>
                        <button class="kit-download-btn text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1" data-id="${item.id}" data-url="${escapeHtml(item.file_url)}">
                            <i data-lucide="download" class="w-3 h-3"></i> Download
                        </button>
                    </div>
                </div>
                <button class="remove-kit-item text-slate-400 hover:text-rose-500 p-1 rounded-lg transition-colors" data-id="${item.id}" title="Remove">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            `;

            div.querySelector("h4")?.addEventListener("click", () => {
                closeStudyKit();
                openPreviewModal(item.id);
            });
            div.querySelector(".kit-preview-btn")?.addEventListener("click", () => {
                closeStudyKit();
                openPreviewModal(item.id);
            });
            div.querySelector(".kit-download-btn")?.addEventListener("click", () => {
                handleDownload(item.id, item.file_url);
            });
            div.querySelector(".remove-kit-item")?.addEventListener("click", async () => {
                await fetch(`/api/bookmarks/${item.id}`, { method: "DELETE", headers: csrfHeaders() });
                state.bookmarks = state.bookmarks.filter((b) => b.id !== item.id);
                updateStudyKitCount();
                renderStudyKit();
                fetchMaterials();
            });

            elements.studyKitItems.appendChild(div);
        });

        if (window.lucide) window.lucide.createIcons();
    }

    // -------------------------------------------------------------
    // Document Preview Modal & Reviews
    // -------------------------------------------------------------
    async function openPreviewModal(id) {
        try {
            const res = await fetch(`/api/materials/${id}`);
            if (!res.ok) throw new Error("Material not found");
            const item = await res.json();
            state.currentPreviewItem = item;

            populatePreviewModal(item);
            elements.previewModal?.classList.remove("hidden");
            document.body.classList.add("overflow-hidden");
        } catch (error) {
            console.error("Failed to load material detail:", error);
            showToast("The document preview could not be opened. Please try again.", "error");
        }
    }

    function populatePreviewModal(item) {
        if (!elements.previewModal) return;

        setReviewRating(0);

        const badgeClass = categoryClasses[item.material_type] || "bg-slate-100 text-slate-800";
        if (elements.previewBadge) {
            elements.previewBadge.className = `inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${badgeClass}`;
            elements.previewBadge.textContent = item.material_type;
        }

        if (elements.previewTitle) elements.previewTitle.textContent = item.title;
        if (elements.previewCode) elements.previewCode.textContent = item.subject_code || "GEN-101";
        if (elements.previewUniversity) elements.previewUniversity.textContent = item.university;
        if (elements.previewSemester) elements.previewSemester.textContent = item.semester;
        if (elements.previewBranch) elements.previewBranch.textContent = item.branch;
        if (elements.previewAuthor) elements.previewAuthor.textContent = `Shared by ${item.uploader_name}`;
        if (elements.previewPages) elements.previewPages.textContent = `${item.page_count || 24} Pages`;
        if (elements.previewSize) elements.previewSize.textContent = `${(item.file_size_kb / 1024).toFixed(1)} MB (${item.file_type || 'PDF'})`;
        if (elements.previewRating) elements.previewRating.textContent = `${item.avg_rating || '5.0'} (${item.review_count || 0} reviews)`;
        if (elements.previewDownloads) elements.previewDownloads.textContent = `${formatNumber(item.downloads_count)} downloads`;
        if (elements.previewDescription) elements.previewDescription.textContent = item.description || "Comprehensive notes for semester exam preparation.";

        // Tags
        if (elements.previewTags) {
            elements.previewTags.innerHTML = "";
            const tags = (item.tags || "").split(",").map((t) => t.trim()).filter(Boolean);
            tags.forEach((tag) => {
                const span = document.createElement("span");
                span.className = "px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-medium";
                span.textContent = `#${tag}`;
                elements.previewTags.appendChild(span);
            });
        }

        // Preview Content
        if (elements.previewContent) {
            elements.previewContent.textContent = item.preview_content || "Direct document download available below.";
        }

        // Action Buttons
        if (elements.previewDownloadBtn) {
            elements.previewDownloadBtn.onclick = () => handleDownload(item.id, item.file_url);
        }

        if (elements.previewBookmarkBtn) {
            const isBookmarked = state.bookmarks.some((b) => b.id === item.id);
            elements.previewBookmarkBtn.innerHTML = `
                <i data-lucide="bookmark" class="w-4 h-4 ${isBookmarked ? 'fill-amber-500 text-amber-500' : ''}"></i>
                <span>${isBookmarked ? 'Saved in Study Kit' : 'Save to Study Kit'}</span>
            `;
            elements.previewBookmarkBtn.onclick = () => {
                handleBookmarkToggle(item, null);
                const updated = state.bookmarks.some((b) => b.id === item.id);
                elements.previewBookmarkBtn.innerHTML = `
                    <i data-lucide="bookmark" class="w-4 h-4 ${updated ? 'fill-amber-500 text-amber-500' : ''}"></i>
                    <span>${updated ? 'Saved in Study Kit' : 'Save to Study Kit'}</span>
                `;
                if (window.lucide) window.lucide.createIcons();
            };
        }

        // Render Reviews
        renderReviewsList(item.reviews || []);

        if (window.lucide) window.lucide.createIcons();
    }

    function closePreviewModal() {
        elements.previewModal?.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
        state.currentPreviewItem = null;
    }

    function renderReviewsList(reviews) {
        if (!elements.reviewsList) return;
        elements.reviewsList.innerHTML = "";

        if (reviews.length === 0) {
            elements.reviewsList.innerHTML = `
                <div class="py-6 text-center text-slate-400 dark:text-slate-500 text-sm">
                    No reviews have been submitted yet. Share your feedback after reviewing this resource.
                </div>
            `;
            return;
        }

        reviews.forEach((r) => {
            const div = document.createElement("div");
            div.className = "p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30";

            let starsHtml = "";
            for (let i = 1; i <= 5; i++) {
                starsHtml += `<i data-lucide="star" class="w-3.5 h-3.5 ${i <= r.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-300 dark:text-slate-600'}"></i>`;
            }

            div.innerHTML = `
                <div class="flex items-center justify-between mb-1.5">
                    <span class="font-bold text-sm text-slate-900 dark:text-white">${escapeHtml(r.author_name)}</span>
                    <div class="flex items-center gap-0.5">${starsHtml}</div>
                </div>
                <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">${escapeHtml(r.comment)}</p>
                <span class="text-[10px] text-slate-400 mt-1.5 block">${r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'}</span>
            `;

            elements.reviewsList.appendChild(div);
        });

        if (window.lucide) window.lucide.createIcons();
    }

    function setReviewRating(rating) {
    const selected = Number(rating);

    if (!Number.isInteger(selected) || selected < 0 || selected > 5) {
        return;
    }

    state.selectedRating = selected;

    elements.starButtons?.forEach((btn) => {
        const starValue = Number(btn.getAttribute("data-star"));
        const active = selected > 0 && starValue <= selected;

        btn.setAttribute("aria-pressed", active ? "true" : "false");

        // Lucide replaces <i> with <svg>, so support both.
        const icon = btn.querySelector("svg, i");

        if (!icon) return;

        if (active) {
            // Selected stars
            icon.classList.add(
                "fill-amber-400",
                "text-amber-400"
            );

            icon.classList.remove(
                "text-slate-300",
                "dark:text-slate-600"
            );
        } else {
            // Unselected stars
            icon.classList.remove(
                "fill-amber-400",
                "text-amber-400"
            );

            icon.classList.add(
                "text-slate-300",
                "dark:text-slate-600"
            );
        }
    });
}

    async function handleReviewSubmit(e) {
        e.preventDefault();
        if (!state.currentPreviewItem) return;

        const commentInput = document.getElementById("reviewCommentInput");

        const comment = commentInput?.value.trim();

        if (state.selectedRating < 1 || state.selectedRating > 5) {
            showToast("Select a rating from 1 to 5 stars before submitting your review.", "error");
            return;
        }

        if (!comment) {
            showToast("Please enter a short comment about this material.", "error");
            return;
        }

        try {
            const res = await fetch(`/api/materials/${state.currentPreviewItem.id}/reviews`, {
                method: "POST",
                headers: csrfHeaders({ "Content-Type": "application/json" }),
                body: JSON.stringify({
                    rating: state.selectedRating,
                    comment: comment
                })
            });

            const data = await res.json();
            if (data.success) {
                showToast("Your review has been submitted.", "success");
                if (commentInput) commentInput.value = "";
                // Refresh modal data
                openPreviewModal(state.currentPreviewItem.id);
                fetchMaterials();
            } else {
                showToast(data.error || "Your review could not be submitted. Please try again.", "error");
            }
        } catch (error) {
            console.error("Review submission error:", error);
            showToast("Your review could not be submitted. Please try again.", "error");
        }
    }

    // -------------------------------------------------------------
    // Download Action Handler
    // -------------------------------------------------------------
   async function handleDownload(id, directUrl) {
    showToast("Preparing your material download...", "info");

    try {
        // First record the download
        const trackRes = await fetch(`/api/materials/${id}/download`, {
            method: "POST",
            headers: csrfHeaders()
        });

        if (!trackRes.ok) {
            throw new Error("Failed to track download");
        }

        // IMPORTANT:
        // Download the ORIGINAL uploaded file from the backend.
        const fileUrl = `/api/materials/${id}/file`;

        const a = document.createElement("a");
        a.href = fileUrl;
        a.download = `UniVault_Material_${id}`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        fetchMaterials();

    } catch (error) {
        console.error("Download failed:", error);
        showToast("The file could not be downloaded. Please try again.", "error");
    }
}
    // -------------------------------------------------------------
    // Upload & Contribution Modal
    // -------------------------------------------------------------
    function openUploadModal() {
        elements.uploadModal?.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");
    }

    function closeUploadModal() {
        elements.uploadModal?.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
        if (elements.uploadForm) elements.uploadForm.reset();
        if (elements.selectedFileName) {
            elements.selectedFileName.textContent = "";
            elements.selectedFileName.classList.add("hidden");
        }
    }

    async function handleUploadSubmit(e) {
        e.preventDefault();
        if (!elements.uploadForm) return;

        const formData = new FormData(elements.uploadForm);
        const title = formData.get("title");
        const subject = formData.get("subject_name");

        if (!title || !subject) {
            showToast("Title and Subject Name are required fields.", "error");
            return;
        }

        if (elements.uploadSubmitBtn) {
            elements.uploadSubmitBtn.disabled = true;
            elements.uploadSubmitBtn.innerHTML = `
                <div class="inline-block animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                Publishing Material...
            `;
        }

        try {
            const res = await fetch("/api/materials", {
                method: "POST",
                headers: csrfHeaders(),
                body: formData
            });

            const data = await res.json();
            if (data.success) {
                showToast("Your resource has been published successfully.", "success");
                closeUploadModal();
                state.page = 1;
                fetchMaterials();
            } else {
                showToast(data.error || "Failed to publish material.", "error");
            }
        } catch (error) {
            console.error("Upload error:", error);
            showToast("Your resource could not be uploaded. Please try again.", "error");
        } finally {
            if (elements.uploadSubmitBtn) {
                elements.uploadSubmitBtn.disabled = false;
                elements.uploadSubmitBtn.innerHTML = `
                    <i data-lucide="upload-cloud" class="w-4 h-4 mr-2"></i>
                    Publish Material
                `;
                if (window.lucide) window.lucide.createIcons();
            }
        }
    }

    // -------------------------------------------------------------
    // Toast Notification System
    // -------------------------------------------------------------
    function showToast(message, type = "info") {
        if (!elements.toastContainer) return;

        const toast = document.createElement("div");
        const bgColors = {
            success: "bg-emerald-600 text-white shadow-emerald-500/20",
            error: "bg-rose-600 text-white shadow-rose-500/20",
            info: "bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-slate-950/20"
        };
        const icons = {
            success: "check-circle",
            error: "alert-circle",
            info: "info"
        };

        toast.className = `flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-sm font-medium toast-enter ${bgColors[type] || bgColors.info}`;
        toast.innerHTML = `
            <i data-lucide="${icons[type] || 'info'}" class="w-4 h-4 flex-shrink-0"></i>
            <span>${escapeHtml(message)}</span>
        `;

        elements.toastContainer.appendChild(toast);
        if (window.lucide) window.lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(10px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // -------------------------------------------------------------
    // Helper Utilities
    // -------------------------------------------------------------
    function formatNumber(num) {
        if (!num) return "0";
        if (num >= 1000) {
            return (num / 1000).toFixed(1).replace(/\.0$/, "") + "k";
        }
        return num.toString();
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Expose controller methods
    window.UniVault = {
        init,
        fetchMaterials,
        openPreviewModal,
        openUploadModal
    };

    // Run on DOM ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
