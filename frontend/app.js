// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentStory = null;
let stories = [];

// Genre names mapping
const genreNames = {
    'Fantasy': '奇幻',
    'Sci-Fi': '科幻',
    'Mystery': '悬疑',
    'Romance': '浪漫',
    'Adventure': '冒险',
    'Horror': '恐怖',
    'Drama': '剧情',
    'Comedy': '喜剧',
    'Thriller': '惊悚',
    'Other': '其他'
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeStoryGenerator();
    initializeStoryList();
    initializeCharacterCounter();
    checkHealth();
});

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            showToast('API服务未启动，请先运行后端服务', 'error');
        }
    } catch (error) {
        showToast('无法连接到API服务', 'error');
    }
}

// Navigation handling
function initializeNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            showPage(page);
        });
    });
}

function showPage(pageName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.page === pageName) {
            btn.classList.add('active');
        }
    });
    
    // Update pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        page.style.display = 'none';
    });
    
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.style.display = 'block';
        setTimeout(() => targetPage.classList.add('active'), 10);
    }
    
    // Load stories if showing list page
    if (pageName === 'list') {
        loadStories();
    }
}

// Character counter
function initializeCharacterCounter() {
    const promptInput = document.getElementById('promptInput');
    const charCount = document.getElementById('charCount');
    
    if (promptInput && charCount) {
        promptInput.addEventListener('input', () => {
            charCount.textContent = promptInput.value.length;
        });
    }
}

// Story Generator
function initializeStoryGenerator() {
    const generateBtn = document.getElementById('generateBtn');
    const regenerateBtn = document.getElementById('regenerateBtn');
    const copyBtn = document.getElementById('copyBtn');
    const clearBtn = document.getElementById('clearBtn');
    const openNotionBtn = document.getElementById('openNotionBtn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', generateStory);
    }
    
    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', generateStory);
    }
    
    if (copyBtn) {
        copyBtn.addEventListener('click', copyStoryContent);
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', clearResult);
    }
    
    if (openNotionBtn) {
        openNotionBtn.addEventListener('click', () => {
            if (currentStory && currentStory.url) {
                window.open(currentStory.url, '_blank');
            }
        });
    }
}

async function generateStory() {
    // Get form values
    const genre = document.querySelector('input[name="genre"]:checked')?.value || 'Fantasy';
    const length = document.querySelector('input[name="length"]:checked')?.value || 'medium';
    const prompt = document.getElementById('promptInput')?.value?.trim();
    
    console.log('=== Story Generation Request ===');
    console.log('Genre:', genre);
    console.log('Genre type:', typeof genre);
    console.log('Length:', length);
    console.log('Length type:', typeof length);
    console.log('Prompt length:', prompt ? prompt.length : 0);
    console.log('Prompt preview:', prompt ? prompt.substring(0, 100) : 'empty');
    
    // Validate input
    if (!prompt) {
        console.error('Validation failed: Empty prompt');
        showToast('请输入创意提示', 'error');
        document.getElementById('promptInput')?.focus();
        return;
    }
    
    if (prompt.length < 10) {
        console.error('Validation failed: Prompt too short');
        showToast('提示词太短，请输入更详细的故事构思', 'error');
        return;
    }
    
    // Show loading
    showLoading(true);
    
    try {
        const requestBody = {
            prompt: prompt,
            genre: genre,
            length: length
        };
        
        console.log('Request body:', JSON.stringify(requestBody, null, 2));
        console.log('Sending request to:', `${API_BASE_URL}/api/stories/generate`);
        
        // Call API
        const response = await fetch(`${API_BASE_URL}/api/stories/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response text:', errorText);
            
            let errorDetail = '生成故事失败';
            try {
                const errorData = JSON.parse(errorText);
                errorDetail = errorData.detail || errorData.message || errorDetail;
            } catch (e) {
                console.error('Failed to parse error response as JSON');
            }
            
            console.error('Error detail:', errorDetail);
            throw new Error(errorDetail);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        currentStory = data.story;
        
        // Display result
        displayStoryResult(currentStory);
        
        // Show regenerate button
        document.getElementById('generateBtn').style.display = 'none';
        document.getElementById('regenerateBtn').style.display = 'inline-flex';
        
        showToast('故事生成成功！', 'success');
        console.log('=== Story Generation Successful ===');
        
    } catch (error) {
        console.error('=== Story Generation Failed ===');
        console.error('Error type:', error.constructor.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        console.error('Full error:', error);
        showToast(`生成失败: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

function displayStoryResult(story) {
    const resultCard = document.getElementById('resultCard');
    const titleEl = document.getElementById('storyTitle');
    const notionLinkEl = document.getElementById('notionLink');
    const genreEl = document.getElementById('storyGenre');
    const wordCountEl = document.getElementById('storyWordCount');
    const contentEl = document.getElementById('storyContent');
    
    // Update content
    titleEl.textContent = story.title || '未命名故事';
    notionLinkEl.href = story.url || '#';
    genreEl.textContent = genreNames[story.genre] || story.genre || '未知';
    wordCountEl.textContent = `${story.word_count || 0} 字`;
    
    // Show preview (first 500 characters)
    const previewLength = 500;
    const content = story.content || '';
    const preview = content.length > previewLength 
        ? content.substring(0, previewLength) + '...' 
        : content;
    contentEl.textContent = preview;
    
    // Show card
    resultCard.style.display = 'block';
    
    // Scroll to result
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function copyStoryContent() {
    if (!currentStory || !currentStory.content) {
        showToast('没有可复制的内容', 'error');
        return;
    }
    
    navigator.clipboard.writeText(currentStory.content)
        .then(() => {
            showToast('内容已复制到剪贴板', 'success');
        })
        .catch(() => {
            showToast('复制失败，请手动复制', 'error');
        });
}

function clearResult() {
    const resultCard = document.getElementById('resultCard');
    const promptInput = document.getElementById('promptInput');
    
    resultCard.style.display = 'none';
    currentStory = null;
    
    document.getElementById('generateBtn').style.display = 'inline-flex';
    document.getElementById('regenerateBtn').style.display = 'none';
    
    if (promptInput) {
        promptInput.value = '';
        document.getElementById('charCount').textContent = '0';
    }
    
    showToast('已清除结果', 'info');
}

// Story List
function initializeStoryList() {
    const refreshBtn = document.getElementById('refreshBtn');
    const filterGenre = document.getElementById('filterGenre');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadStories);
    }
    
    if (filterGenre) {
        filterGenre.addEventListener('change', () => {
            displayStories();
        });
    }
}

async function loadStories() {
    const storyListEl = document.getElementById('storyList');
    
    // Show loading
    storyListEl.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/stories`);
        
        if (!response.ok) {
            throw new Error('加载故事列表失败');
        }
        
        const data = await response.json();
        stories = data.stories || [];
        
        displayStories();
        
    } catch (error) {
        console.error('Error loading stories:', error);
        showToast(`加载失败: ${error.message}`, 'error');
        storyListEl.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <div class="empty-state-text">加载失败，请刷新重试</div>
            </div>
        `;
    }
}

function displayStories() {
    const storyListEl = document.getElementById('storyList');
    const filterGenre = document.getElementById('filterGenre')?.value || '';
    
    // Filter stories
    let filteredStories = stories;
    if (filterGenre) {
        filteredStories = stories.filter(s => s.genre === filterGenre);
    }
    
    // Empty state
    if (filteredStories.length === 0) {
        storyListEl.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">
                    ${stories.length === 0 ? '还没有生成过故事，快去创作吧！' : '没有找到该类型的故事'}
                </div>
            </div>
        `;
        return;
    }
    
    // Build list
    storyListEl.innerHTML = filteredStories.map(story => `
        <div class="story-item" onclick="openStory('${story.id}')">
            <div class="story-item-info">
                <div class="story-item-title">${escapeHtml(story.title || '未命名故事')}</div>
                <div class="story-item-meta">
                    <span>📚 ${genreNames[story.genre] || story.genre || '未知'}</span>
                    <span>📝 ${story.word_count || 0} 字</span>
                    ${story.created_at ? `<span>🕐 ${formatDate(story.created_at)}</span>` : ''}
                </div>
            </div>
            <div class="story-item-actions">
                <button class="btn btn-small" onclick="event.stopPropagation(); openStoryUrl('${story.url}')" ${!story.url ? 'disabled' : ''}>
                    🔗
                </button>
                <button class="btn btn-small btn-danger" onclick="event.stopPropagation(); deleteStory('${story.id}')">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
}

function openStory(storyId) {
    const story = stories.find(s => s.id === storyId);
    if (story && story.content) {
        // Display in result card
        currentStory = story;
        displayStoryResult(story);
        
        // Switch to generate page
        showPage('generate');
        
        showToast('已加载故事内容', 'info');
    } else {
        showToast('无法加载故事内容', 'error');
    }
}

function openStoryUrl(url) {
    if (url) {
        window.open(url, '_blank');
    } else {
        showToast('该故事没有Notion链接', 'error');
    }
}

async function deleteStory(storyId) {
    if (!confirm('确定要删除这个故事吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/stories/${storyId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('删除失败');
        }
        
        showToast('故事已删除', 'success');
        
        // Reload list
        loadStories();
        
    } catch (error) {
        console.error('Error deleting story:', error);
        showToast(`删除失败: ${error.message}`, 'error');
    }
}

// Utility functions
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    // Set message and type
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}