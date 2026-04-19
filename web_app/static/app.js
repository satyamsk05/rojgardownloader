async function fetchInfo() {
    const urlInput = document.getElementById('url');
    const url = urlInput.value.trim();
    const btn = document.getElementById('fetch-btn');
    const preview = document.getElementById('preview');
    
    if (!url) return;
    
    // UI Loading state
    btn.innerHTML = 'Analyzing... <span class="material-symbols-outlined animate-spin text-sm">progress_activity</span>';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/info', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url})
        });
        const data = await res.json();
        
        if (data.title) {
            // Show preview with transition
            preview.classList.add('show');
            
            // Use proxy for thumbnail
            const proxyThumb = `/api/proxy-image?url=${encodeURIComponent(data.thumbnail)}`;
            document.getElementById('thumb').src = proxyThumb;
            document.getElementById('title').innerText = data.title;
            
            // Refined meta badges (Light Mode)
            const durationText = `${Math.floor(data.duration / 60)}m ${data.duration % 60}s`;
            document.getElementById('meta').innerHTML = `
                <div class="px-4 py-2.5 bg-black/5 backdrop-blur-md rounded-xl text-[10px] font-black flex items-center gap-2 border border-black/5 uppercase tracking-[0.2em] text-black/40">
                    <span class="material-symbols-outlined text-sm">account_circle</span> ${data.uploader}
                </div>
                <div class="px-4 py-2.5 bg-black/5 backdrop-blur-md rounded-xl text-[10px] font-black flex items-center gap-2 border border-black/5 uppercase tracking-[0.2em] text-black/40">
                    <span class="material-symbols-outlined text-sm">schedule</span> ${durationText}
                </div>
            `;

            // Populate format dropdown dynamically
            const formatSelect = document.getElementById('format-select');
            formatSelect.innerHTML = '<option value="auto">✨ Best Quality (Auto-detect)</option>';
            if (data.formats && data.formats.length > 0) {
                data.formats.forEach(f => {
                    const mergeNote = f.needs_merge 
                        ? ' ⚡ (server merge — slower)' 
                        : ' 🔗 (direct stream — fast)';
                    const opt = document.createElement('option');
                    opt.value = f.format_id;
                    opt.textContent = `${f.label}${mergeNote}`;
                    formatSelect.appendChild(opt);
                });
                // Audio only
                const audioOpt = document.createElement('option');
                audioOpt.value = 'bestaudio[ext=m4a]/bestaudio/best';
                audioOpt.textContent = '🎵 Audio Only (M4A) 🔗 direct';
                formatSelect.appendChild(audioOpt);
            }
            
            // Smooth scroll with offset
            setTimeout(() => {
                const headerHeight = 150;
                const elementPosition = preview.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerHeight;
                window.scrollTo({ top: offsetPosition, behavior: "smooth" });
            }, 100);
            
            // Set up download button
            const dlBtn = document.getElementById('dl-btn');
            dlBtn.onclick = () => triggerDownload(url);
        } else {
            showToast("Could not find video info. Check the URL.", "error");
        }
    } catch (err) {
        showToast("Error connecting to server.", "error");
    } finally {
        btn.innerHTML = 'Curate <span class="material-symbols-outlined font-black">arrow_forward</span>';
        btn.disabled = false;
    }
}

async function triggerDownload(url) {
    const dlBtn = document.getElementById('dl-btn');
    const formatId = document.getElementById('format-select').value;
    
    // Build GET URL — browser handles download natively (shows Chrome download bar immediately)
    const params = new URLSearchParams({ url, format_id: formatId });
    const downloadUrl = `/api/download?${params.toString()}`;
    
    // Show brief loading state
    const originalHtml = dlBtn.innerHTML;
    dlBtn.innerHTML = '<span class="material-symbols-outlined animate-bounce">downloading</span> Starting...';
    dlBtn.disabled = true;
    
    // Trigger native browser download
    window.location.href = downloadUrl;
    
    showToast("Download started! Check Chrome's download bar ↓", "info");
    saveToHistory(document.getElementById('title').innerText, document.getElementById('thumb').src, url);
    
    // Re-enable button after a moment
    setTimeout(() => {
        dlBtn.innerHTML = originalHtml;
        dlBtn.disabled = false;
    }, 3000);
}

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'error' ? 'bg-red-500' : type === 'info' ? 'bg-blue-600' : 'bg-black';
    const icon = type === 'error' ? 'error' : type === 'info' ? 'info' : 'check_circle';
    toast.className = `${bg} text-white px-6 py-3 rounded-full text-sm font-semibold shadow-xl flex items-center gap-2 transform transition-all duration-300 -translate-y-full opacity-0`;
    toast.innerHTML = `<span class="material-symbols-outlined text-sm">${icon}</span> ${message}`;
    container.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.classList.remove('-translate-y-full', 'opacity-0');
    });
    
    setTimeout(() => {
        toast.classList.add('-translate-y-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Download History
function saveToHistory(title, thumb, url) {
    let history = JSON.parse(localStorage.getItem('rojger_history') || '[]');
    // Avoid duplicates
    history = history.filter(item => item.url !== url);
    history.unshift({title, thumb, url, date: new Date().toISOString()});
    history = history.slice(0, 4); // Keep last 4
    localStorage.setItem('rojger_history', JSON.stringify(history));
    renderHistory();
}

function renderHistory() {
    const history = JSON.parse(localStorage.getItem('rojger_history') || '[]');
    const section = document.getElementById('history-section');
    const list = document.getElementById('history-list');
    
    if (history.length === 0) return;
    
    section.classList.remove('hidden');
    list.innerHTML = history.map(item => `
        <div class="bg-white/50 p-4 rounded-3xl flex items-center gap-4 border border-white shadow-sm cursor-pointer hover:scale-105 transition-transform" onclick="document.getElementById('url').value='${item.url}'; fetchInfo(); window.scrollTo({top: 0, behavior: 'smooth'});">
            <img src="${item.thumb}" class="w-16 h-16 rounded-2xl object-cover" />
            <div class="overflow-hidden">
                <h5 class="font-black text-sm truncate">${item.title}</h5>
                <p class="text-[10px] text-black/40 font-bold uppercase tracking-widest mt-1">${new Date(item.date).toLocaleDateString()}</p>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', renderHistory);
