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
                <div class="px-6 py-3 bg-black/5 backdrop-blur-md rounded-2xl text-[10px] font-black flex items-center gap-2 border border-black/5 uppercase tracking-[0.2em] text-black/40">
                    <span class="material-symbols-outlined text-sm">account_circle</span> ${data.uploader}
                </div>
                <div class="px-6 py-3 bg-black/5 backdrop-blur-md rounded-2xl text-[10px] font-black flex items-center gap-2 border border-black/5 uppercase tracking-[0.2em] text-black/40">
                    <span class="material-symbols-outlined text-sm">schedule</span> ${durationText}
                </div>
            `;
            
            // Smooth scroll with offset
            setTimeout(() => {
                const headerHeight = 150;
                const elementPosition = preview.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerHeight;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: "smooth"
                });
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
    const originalHtml = dlBtn.innerHTML;
    const formatId = document.getElementById('format-select').value;
    
    dlBtn.innerHTML = '<span class="material-symbols-outlined animate-bounce">downloading</span> PROCESSING <span id="dl-progress"></span>';
    dlBtn.disabled = true;
    
    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url, format_id: formatId})
        });
        
        if (res.ok) {
            let filename = "video.mp4";
            const disposition = res.headers.get('content-disposition');
            if (disposition && disposition.includes("filename*=UTF-8''")) {
                filename = decodeURIComponent(disposition.split("filename*=UTF-8''")[1]);
            }
            
            const contentLength = res.headers.get('content-length');
            const total = contentLength ? parseInt(contentLength, 10) : 0;
            let loaded = 0;
            
            const reader = res.body.getReader();
            const chunks = [];
            
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                chunks.push(value);
                loaded += value.length;
                
                if (total) {
                    const percent = Math.round((loaded / total) * 100);
                    document.getElementById('dl-progress').innerText = `(${percent}%)`;
                } else {
                    const mb = (loaded / (1024*1024)).toFixed(1);
                    document.getElementById('dl-progress').innerText = `(${mb} MB)`;
                }
            }
            
            const blob = new Blob(chunks);
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            
            showToast("Curated successfully!");
            saveToHistory(document.getElementById('title').innerText, document.getElementById('thumb').src, url);
        } else {
            showToast("Download failed. Try another link.", "error");
        }
    } catch (err) {
        showToast("Server error during download.", "error");
    } finally {
        dlBtn.innerHTML = originalHtml;
        dlBtn.disabled = false;
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'error' ? 'bg-red-500' : 'bg-black';
    toast.className = `${bg} text-white px-6 py-3 rounded-full text-sm font-semibold shadow-xl flex items-center gap-2 transform transition-all duration-300 -translate-y-full opacity-0`;
    toast.innerHTML = `<span class="material-symbols-outlined text-sm">${type === 'error' ? 'error' : 'check_circle'}</span> ${message}`;
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
