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
            alert("Could not find video info. Check the URL.");
        }
    } catch (err) {
        alert("Error connecting to server.");
    } finally {
        btn.innerHTML = 'Curate <span class="material-symbols-outlined font-black">arrow_forward</span>';
        btn.disabled = false;
    }
}

async function triggerDownload(url) {
    const dlBtn = document.getElementById('dl-btn');
    const originalHtml = dlBtn.innerHTML;
    
    dlBtn.innerHTML = '<span class="material-symbols-outlined animate-bounce">downloading</span> PROCESSING...';
    dlBtn.disabled = true;
    
    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url})
        });
        
        if (res.ok) {
            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = "video.mp4";
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert("Download failed. Try another link.");
        }
    } catch (err) {
        alert("Server error during download.");
    } finally {
        dlBtn.innerHTML = originalHtml;
        dlBtn.disabled = false;
    }
}
