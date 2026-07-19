<template>
  <div class="app-shell" :class="'theme-' + theme">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark-wrapper">
          <div class="brand-mark-ring"></div>
          <div class="brand-mark">AI</div>
        </div>
        <div class="brand-text">
          <h1>{{ t('siteTitle') }}</h1>
          <p>{{ t('subtitle') }}</p>
        </div>
      </div>
      <div class="topbar-actions">
        <div class="preference-group">
          <div class="lang-switch">
            <button :class="{ active: lang === 'zh' }" @click="switchLang('zh')">中文</button>
            <span class="lang-sep">|</span>
            <button :class="{ active: lang === 'en' }" @click="switchLang('en')">EN</button>
          </div>
          <button
            class="theme-toggle"
            type="button"
            :aria-label="themeToggleLabel"
            :title="themeToggleLabel"
            @click="toggleTheme"
          >
            <span>{{ themeToggleIcon }}</span>
          </button>
        </div>
        <div
          class="update-chip"
          :class="{ 'update-chip--compact-mobile': lang === 'en' }"
          :title="countdownFullText"
          :aria-label="countdownFullText"
        >
          <span class="update-chip-icon">⏱</span>
          <span class="update-chip-text">{{ countdownText }}</span>
        </div>
        <div class="utility-group">
          <button class="history-button" type="button" @click="openHistoryDrawer">
            {{ t('historyArchive') }}
          </button>
          <a class="gh-link" href="https://github.com/wenbochang888/github-trending-spider" target="_blank" rel="noreferrer" aria-label="GitHub 仓库">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
          </a>
        </div>
      </div>
    </header>

    <div
      class="history-drawer-mask"
      :class="{ open: historyDrawerOpen }"
      @click="closeHistoryDrawer"
    >
      <aside class="history-drawer" @click.stop>
        <div class="history-drawer-head">
          <div>
            <h2>{{ t('historyDrawerTitle') }}</h2>
            <p>{{ t('historyDrawerDesc') }}</p>
          </div>
          <button class="history-drawer-close" type="button" @click="closeHistoryDrawer">×</button>
        </div>

        <div v-if="historyDatesLoading" class="history-drawer-state">
          {{ t('historyLoading') }}
        </div>
        <div v-else-if="historyDatesError" class="history-drawer-state error">
          {{ historyDatesError }}
        </div>
        <div v-else class="history-date-list">
          <button
            v-for="dateInfo in historyDates"
            :key="dateInfo.date"
            class="history-date-row"
            :class="{
              active: selectedHistoryDate === dateInfo.date,
              disabled: !dateInfo.has_archive
            }"
            type="button"
            :disabled="!dateInfo.has_archive"
            @click="selectHistoryDate(dateInfo)"
          >
            <strong>{{ formatHistoryDate(dateInfo.date) }}</strong>
            <span>{{ getHistoryDateSummary(dateInfo) }}</span>
          </button>
        </div>
      </aside>
    </div>

    <main class="layout">
      <aside class="source-panel">
        <button
          class="source-tab"
          :class="{ active: podcastMode }"
          type="button"
          @click="selectPodcast"
        >
          <span>{{ t('podcastNavLabel') }}</span>
          <small>{{ t('podcastNavCategory') }}</small>
        </button>
        <button
          v-for="source in sources"
          :key="source.id"
          class="source-tab"
          :class="{ active: source.id === activeSourceId }"
          type="button"
          @click="selectSource(source.id)"
        >
          <span>{{ getDisplayLabel(source) }}</span>
          <small>{{ getDisplayCategory(source) }}</small>
        </button>
      </aside>

      <section class="feed-panel">
        <div class="feed-toolbar">
          <div>
            <h2>{{ feedTitle }}</h2>
            <p v-if="feedSubtitle" class="feed-subtitle">{{ feedSubtitle }}</p>
          </div>
          <button
            v-if="historyMode"
            class="back-today-button"
            type="button"
            @click="backToToday"
          >
            {{ t('backToToday') }}
          </button>
        </div>

        <div v-if="podcastMode" class="podcast-view">
          <div v-if="podcastLoading" class="skeleton-list">
            <div v-for="n in 2" :key="n" class="skeleton-card">
              <div class="skeleton-line title"></div>
              <div class="skeleton-line body"></div>
              <div class="skeleton-line body short"></div>
            </div>
          </div>
          <div v-else-if="podcastError" class="state-box error">{{ podcastError }}</div>
          <div v-else-if="!latestPodcast" class="state-box">
            {{ t('podcastEmpty') }}
          </div>
          <div v-else>
            <section class="podcast-episode">
              <div class="podcast-episode-main">
                <span class="podcast-kicker">{{ t('podcastKicker') }}</span>
                <h3>{{ latestPodcast.title }}</h3>
                <p class="podcast-summary">{{ t('podcastSummary') }}</p>
                <div class="podcast-meta-row">
                  <span>{{ latestPodcast.date }}</span>
                  <span>{{ formatDuration(latestPodcast.duration_seconds) }}</span>
                  <span>{{ latestPodcast.source_count }} {{ t('podcastSources') }}</span>
                  <span>{{ latestPodcast.item_count }} {{ t('podcastItems') }}</span>
                </div>
                <audio
                  class="podcast-player"
                  controls
                  preload="none"
                  :src="latestPodcast.audio_url"
                ></audio>
              </div>
              <aside class="podcast-chapters" v-if="latestPodcast.chapters && latestPodcast.chapters.length">
                <h4>{{ t('podcastChapters') }}</h4>
                <div
                  v-for="chapter in latestPodcast.chapters"
                  :key="chapter.time + chapter.title"
                  class="podcast-chapter"
                >
                  <span>{{ chapter.time }}</span>
                  <strong>{{ chapter.title }}</strong>
                </div>
              </aside>
            </section>
          </div>
        </div>
        <template v-else>
          <div v-if="loading" class="skeleton-list">
            <div v-for="n in 3" :key="n" class="skeleton-card">
              <div class="skeleton-line title"></div>
              <div class="skeleton-line body"></div>
              <div class="skeleton-line body short"></div>
            </div>
          </div>
          <div v-else-if="errorMessage" class="state-box error">{{ errorMessage }}</div>
          <div v-else-if="items.length === 0" class="state-box">
            {{ t('noContent') }}
          </div>

          <article
            v-for="item in items"
            v-else
            :key="item.url + item.title"
            class="feed-item"
          >
            <div class="item-main">
              <a class="item-title" :href="item.url" target="_blank" rel="noreferrer">
                {{ item.title }}
              </a>
              <p class="item-summary">{{ getDisplaySummary(item) }}</p>
              <div class="item-tags" v-if="getItemTags(item).length">
                <span
                  v-for="tag in getItemTags(item)"
                  :key="tag.label"
                  class="item-tag"
                  :class="'item-tag--' + tag.type"
                >
                  <span v-if="tag.dotColor" class="lang-dot" :style="{ background: tag.dotColor }"></span>
                  {{ tag.label }}
                </span>
              </div>
            </div>
            <a
              class="open-link"
              :href="getOpenUrl(item)"
              target="_blank"
              rel="noreferrer"
            >
              {{ isDiscussion(item) ? t('viewDiscussion') : t('readOriginal') }}
            </a>
          </article>
        </template>
      </section>
    </main>
    <footer class="site-footer">
      <button class="footer-easter-egg" type="button" @click="showEmailHint">
        {{ t('footerEmailEgg') }}
      </button>
    </footer>
  </div>
</template>

<script>
const API_PREFIX = '/api';
const PODCAST_SOURCE_ID = '__podcast__';
const THEME_STORAGE_KEY = 'theme';
const MOBILE_LAYOUT_QUERY = '(max-width: 860px)';

// ── i18n：语言优先级 URL 参数 > localStorage > 默认 'zh' ──
function getInitialLang() {
  const params = new URLSearchParams(window.location.search);
  const urlLang = params.get('lang');
  if (urlLang === 'en' || urlLang === 'zh') return urlLang;
  const stored = localStorage.getItem('lang');
  if (stored === 'en' || stored === 'zh') return stored;
  return 'zh';
}

function getInitialTheme() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;

  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

const I18N = {
  zh: {
    siteTitle: '每日AI前沿信息',
    subtitle: '开源趋势 · 社区热议 · AI 动态',
    updateEvery8h: '每 8 小时更新',
    countdownHour: '时',
    countdownMin: '分',
    countdownSec: '秒',
    countdownSuffix: '后更新',
    noContent: '当前来源暂无内容',
    loadSourceErr: '加载来源失败：',
    loadContentErr: '加载内容失败：',
    sourceApiErr: '来源接口返回 ',
    dataApiErr: '数据接口返回 ',
    historyApiErr: '历史接口返回 ',
    readOriginal: '阅读原文 →',
    viewDiscussion: '查看讨论 →',
    defaultLabel: '最新内容',
    historyArchive: '历史归档',
    historyDrawerTitle: '历史归档',
    historyDrawerDesc: '最近 7 天，不包含今天。选择日期后读取当天历史资讯。',
    historyLoading: '正在加载历史归档',
    historyLoadErr: '加载历史归档失败：',
    historyTitle: '历史资讯',
    backToToday: '返回今日资讯',
    noArchive: '暂无归档',
    archiveSources: ' 个来源',
    historySourcePrefix: '当前来源：',
    footerEmailEgg: '隐藏小彩蛋: 支持邮件接收AI讯息',
    emailHint: '请将您的邮箱发送至727987105@qq.com',
    switchToDark: '切换到深色模式',
    switchToLight: '切换到浅色模式',
    comments: ' 评论',
    replies: ' 回复',
    podcastNavLabel: '今日 AI 播客',
    podcastNavCategory: '自动音频日报',
    podcastTitle: '今日 AI 播客',
    podcastEmpty: '今日播客生成中',
    podcastLoadErr: '加载播客失败：',
    podcastKicker: '最新一期 · 自动生成',
    podcastSummary: '基于昨日重点资讯生成男女对话音频，快速回顾开源热点、社区讨论和官方更新。',
    podcastSources: '个来源',
    podcastItems: '条内容',
    podcastChapters: '本期章节',
  },
  en: {
    siteTitle: 'Daily AI Frontier',
    subtitle: 'Open Source · Community · AI Updates',
    updateEvery8h: 'Updates every 8h',
    countdownHour: 'h ',
    countdownMin: 'm ',
    countdownSec: 's',
    countdownSuffix: ' until next update',
    noContent: 'No content available for this source',
    loadSourceErr: 'Failed to load sources: ',
    loadContentErr: 'Failed to load content: ',
    sourceApiErr: 'Sources API returned ',
    dataApiErr: 'Data API returned ',
    historyApiErr: 'History API returned ',
    readOriginal: 'Read More →',
    viewDiscussion: 'View Discussion →',
    defaultLabel: 'Latest',
    historyArchive: 'Archive',
    historyDrawerTitle: 'Archive',
    historyDrawerDesc: 'Last 7 days, excluding today. Pick a date to read archived news.',
    historyLoading: 'Loading archive',
    historyLoadErr: 'Failed to load archive: ',
    historyTitle: 'Archive',
    backToToday: 'Back to Today',
    noArchive: 'No archive',
    archiveSources: ' sources',
    historySourcePrefix: 'Source: ',
    footerEmailEgg: 'Hidden easter egg: Support receiving AI updates by email',
    emailHint: 'Please send your email address to 727987105@qq.com',
    switchToDark: 'Switch to dark mode',
    switchToLight: 'Switch to light mode',
    comments: ' comments',
    replies: ' replies',
    podcastNavLabel: 'Daily AI Podcast',
    podcastNavCategory: 'Auto audio digest',
    podcastTitle: 'Daily AI Podcast',
    podcastEmpty: 'Podcast is being generated',
    podcastLoadErr: 'Failed to load podcast: ',
    podcastKicker: 'Latest episode · Auto-generated',
    podcastSummary: 'A two-host audio digest of yesterday’s key open-source trends, community discussions, and official AI updates.',
    podcastSources: 'sources',
    podcastItems: 'items',
    podcastChapters: 'Chapters',
  }
};

const SOURCE_DISPLAY_MAP = {
  'github-daily':  { label: '今日开源热榜', category: 'GitHub · 日榜' },
  'github-weekly': { label: '本周开源精选', category: 'GitHub · 周榜' },
  'hacker-news':   { label: '硅谷社区热议', category: 'Hacker News'   },
  // 上游日报停止更新，暂时停用；恢复来源注册时同步取消注释。
  // 'linux-do':      { label: 'Linux.do 技术日报', category: '社区讨论'     },
  'v2ex':          { label: 'V2EX 技术日报', category: 'V2EX'          },
  'tldr-ai':       { label: 'AI 速报精选',   category: 'TLDR AI'       },
  'openai':        { label: 'OpenAI 最新动态', category: '官方更新'    },
  'anthropic':     { label: 'Anthropic 最新动态', category: '官方更新' },
  'infoq':         { label: 'AI 工程实践',    category: 'InfoQ AI'     },
};

const TLDR_CATEGORY_MAP = {
  'BIG TECH & STARTUPS': '大厂动态',
  'SCIENCE & FUTURISTIC TECHNOLOGY': '前沿科技',
  'PROGRAMMING, DESIGN & DATA SCIENCE': '编程与数据',
  'AI': 'AI 快讯',
};

const CONTENT_TYPE_MAP = {
  'Product': '产品发布',
  'Research': '研究',
  'Safety': '安全',
  'Announcements': '公告',
  'Company': '公司动态',
};

const INFOQ_CATEGORY_MAP = {
  'InfoQ Artificial Intelligence': '人工智能',
  'InfoQ Generative AI': '生成式 AI',
  'InfoQ AI Development': 'AI 工程实践',
  'AI 工程实践': 'AI 工程实践',
  'Artificial Intelligence': '人工智能',
  'Generative AI': '生成式 AI',
  'AI Development': 'AI 工程实践',
  'Machine Learning': '机器学习',
};

// ── 英文版来源映射 ──
const SOURCE_DISPLAY_MAP_EN = {
  'github-daily':  { label: 'GitHub Daily Trending', category: 'GitHub · Daily' },
  'github-weekly': { label: 'GitHub Weekly Picks',   category: 'GitHub · Weekly' },
  'hacker-news':   { label: 'Hacker News Hot',       category: 'Hacker News' },
  // Upstream digest is no longer updated. Keep this mapping for future recovery.
  // 'linux-do':      { label: 'Linux.do Daily',        category: 'Community' },
  'v2ex':          { label: 'V2EX Hot Topics',       category: 'V2EX' },
  'tldr-ai':       { label: 'TLDR AI Digest',        category: 'TLDR AI' },
  'openai':        { label: 'OpenAI Updates',        category: 'Official' },
  'anthropic':     { label: 'Anthropic Updates',     category: 'Official' },
  'infoq':         { label: 'AI Engineering',        category: 'InfoQ AI' },
};

const LANGUAGE_COLORS = {
  'JavaScript':       '#f1e05a',
  'TypeScript':       '#3178c6',
  'Python':           '#3572A5',
  'Go':               '#00ADD8',
  'Rust':             '#dea584',
  'Java':             '#b07219',
  'C++':              '#f34b7d',
  'C':                '#555555',
  'C#':               '#178600',
  'Ruby':             '#701516',
  'Swift':            '#F05138',
  'Kotlin':           '#A97BFF',
  'Shell':            '#89e051',
  'HTML':             '#e34c26',
  'CSS':              '#563d7c',
  'Vue':              '#41b883',
  'PHP':              '#4F5D95',
  'Scala':            '#c22d40',
  'Dart':             '#00B4AB',
  'Elixir':           '#6e4a7e',
  'Haskell':          '#5e5086',
  'Lua':              '#000080',
  'R':                '#198CE7',
  'Jupyter Notebook': '#DA5B0B',
  'CUDA':             '#3A4E3A',
  'Makefile':         '#427819',
  'Nix':              '#7e7eff',
  'Zig':              '#ec915c',
  'OCaml':            '#ef7a08',
  'Perl':             '#0298c3',
  'Dockerfile':       '#384d54',
};

// 每日定时更新时间（24小时制）
const SCHEDULE_TIMES = [
  { hour: 7, minute: 50 },
  { hour: 15, minute: 50 },
  { hour: 23, minute: 50 },
];

export default {
  name: 'App',
  data() {
    return {
      lang: getInitialLang(),
      theme: getInitialTheme(),
      sources: [],
      activeSourceId: '',
      items: [],
      generatedAt: '',
      loading: false,
      errorMessage: '',
      historyDrawerOpen: false,
      historyDates: [],
      historyDatesLoading: false,
      historyDatesError: '',
      historyMode: false,
      selectedHistoryDate: '',
      latestPodcast: null,
      podcastLoading: false,
      podcastError: '',
      countdownText: '',
      countdownFullText: '',
      countdownTimer: null
    };
  },
  computed: {
    activeSourceLabel() {
      const map = this.lang === 'en' ? SOURCE_DISPLAY_MAP_EN : SOURCE_DISPLAY_MAP;
      const override = map[this.activeSourceId];
      if (override) return override.label;
      const source = this.sources.find((s) => s.id === this.activeSourceId);
      return source ? source.label : this.t('defaultLabel');
    },
    podcastMode() {
      return this.activeSourceId === PODCAST_SOURCE_ID;
    },
    feedTitle() {
      if (this.podcastMode) {
        return this.t('podcastTitle');
      }
      if (this.historyMode && this.selectedHistoryDate) {
        return `${this.t('historyTitle')} · ${this.selectedHistoryDate}`;
      }
      return this.activeSourceLabel;
    },
    feedSubtitle() {
      if (this.podcastMode) {
        return '';
      }
      if (!this.historyMode) {
        return '';
      }
      return `${this.t('historySourcePrefix')}${this.activeSourceLabel}`;
    },
    themeToggleLabel() {
      return this.theme === 'dark' ? this.t('switchToLight') : this.t('switchToDark');
    },
    themeToggleIcon() {
      return this.theme === 'dark' ? '☀' : '☾';
    }
  },
  async created() {
    document.title = this.t('siteTitle');
    this.countdownText = this.t('updateEvery8h');
    this.countdownFullText = this.t('updateEvery8h');
    await this.loadSources();
  },
  mounted() {
    this.updateCountdown();
    this.countdownTimer = setInterval(() => {
      this.updateCountdown();
    }, 1000);
  },
  beforeUnmount() {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }
  },
  methods: {
    t(key) {
      return (I18N[this.lang] && I18N[this.lang][key]) || I18N['zh'][key] || key;
    },
    switchLang(newLang) {
      this.lang = newLang;
      localStorage.setItem('lang', newLang);
      const url = new URL(window.location);
      url.searchParams.set('lang', newLang);
      history.replaceState(null, '', url);
      document.title = this.t('siteTitle');
      this.updateCountdown();
    },
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem(THEME_STORAGE_KEY, this.theme);
    },
    showEmailHint() {
      window.alert(this.t('emailHint'));
    },
    async openHistoryDrawer() {
      this.historyDrawerOpen = true;
      if (this.historyDates.length === 0 && !this.historyDatesLoading) {
        await this.loadHistoryDates();
      }
    },
    closeHistoryDrawer() {
      this.historyDrawerOpen = false;
    },
    resetFeedScroll() {
      if (window.matchMedia && window.matchMedia(MOBILE_LAYOUT_QUERY).matches) {
        return;
      }

      const feedPanel = document.querySelector('.feed-panel');
      if (!feedPanel) {
        window.scrollTo({ top: 0, behavior: 'auto' });
        return;
      }

      const targetTop = window.scrollY + feedPanel.getBoundingClientRect().top - 84;
      window.scrollTo({ top: Math.max(0, targetTop), behavior: 'auto' });
    },
    async loadHistoryDates() {
      this.historyDatesLoading = true;
      this.historyDatesError = '';
      try {
        const response = await fetch(`${API_PREFIX}/history/dates`);
        if (!response.ok) {
          throw new Error(`${this.t('historyApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.historyDates = payload.dates || [];
      } catch (error) {
        this.historyDates = [];
        this.historyDatesError = `${this.t('historyLoadErr')}${error.message}`;
      } finally {
        this.historyDatesLoading = false;
      }
    },
    async selectHistoryDate(dateInfo) {
      if (!dateInfo || !dateInfo.has_archive) {
        return;
      }
      this.selectedHistoryDate = dateInfo.date;
      this.historyMode = true;
      this.historyDrawerOpen = false;
      await this.loadHistorySource(this.activeSourceId);
    },
    async loadHistorySource(sourceId) {
      this.activeSourceId = sourceId;
      this.loading = true;
      this.errorMessage = '';
      let shouldResetScroll = false;
      try {
        const response = await fetch(`${API_PREFIX}/history/sources/${sourceId}/dates/${this.selectedHistoryDate}`);
        if (!response.ok) {
          throw new Error(`${this.t('dataApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.items = payload.items || [];
        this.generatedAt = payload.generated_at || '';
        shouldResetScroll = true;
      } catch (error) {
        this.items = [];
        this.generatedAt = '';
        this.errorMessage = `${this.t('loadContentErr')}${error.message}`;
        shouldResetScroll = true;
      } finally {
        this.loading = false;
      }
      if (shouldResetScroll) {
        await this.$nextTick();
        this.resetFeedScroll();
      }
    },
    async backToToday() {
      this.historyMode = false;
      this.selectedHistoryDate = '';
      await this.selectSource(this.activeSourceId);
    },
    async selectPodcast() {
      this.activeSourceId = PODCAST_SOURCE_ID;
      this.historyMode = false;
      this.selectedHistoryDate = '';
      this.items = [];
      this.errorMessage = '';
      await this.loadPodcast();
      await this.$nextTick();
      this.resetFeedScroll();
    },
    async loadPodcast() {
      this.podcastLoading = true;
      this.podcastError = '';
      try {
        const latestResponse = await fetch(`${API_PREFIX}/podcast/latest`);
        if (!latestResponse.ok) {
          throw new Error(`${this.t('dataApiErr')}${latestResponse.status}`);
        }
        const latestPayload = await latestResponse.json();
        this.latestPodcast = latestPayload.podcast || null;
      } catch (error) {
        this.latestPodcast = null;
        this.podcastError = `${this.t('podcastLoadErr')}${error.message}`;
      } finally {
        this.podcastLoading = false;
      }
    },
    formatDuration(seconds) {
      const totalSeconds = Number(seconds || 0);
      if (!totalSeconds) {
        return this.lang === 'en' ? 'Unknown duration' : '时长未知';
      }
      const minutes = Math.floor(totalSeconds / 60);
      const restSeconds = totalSeconds % 60;
      if (this.lang === 'en') {
        return `${minutes}m ${restSeconds}s`;
      }
      return `${minutes}分${restSeconds}秒`;
    },
    formatHistoryDate(dateText) {
      if (!dateText) {
        return '';
      }
      return dateText.slice(5);
    },
    getHistoryDateSummary(dateInfo) {
      if (!dateInfo.has_archive) {
        return this.t('noArchive');
      }
      return `${dateInfo.source_count}${this.t('archiveSources')}`;
    },
    getDisplaySummary(item) {
      if (this.lang === 'zh') {
        return item.chinese_summary || item.original_summary || '';
      }
      let text = item.original_summary || item.chinese_summary || '';
      // 替换后端 original_summary 中的中文标签为英文
      text = text.replace(/语言:\s*/g, 'Language: ');
      text = text.replace(/分数:\s*/g, 'Score: ');
      text = text.replace(/评论数:\s*/g, 'Comments: ');
      text = text.replace(/作者:\s*/g, 'Author: ');
      text = text.replace(/节点:\s*/g, 'Node: ');
      text = text.replace(/分组:\s*/g, 'Section: ');
      text = text.replace(/回复数:\s*/g, 'Replies: ');
      return text;
    },
    updateCountdown() {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      let nextUpdate = null;

      // 找今天剩余的更新时间
      for (const t of SCHEDULE_TIMES) {
        const candidate = new Date(today.getTime() + t.hour * 3600000 + t.minute * 60000);
        if (candidate > now) {
          nextUpdate = candidate;
          break;
        }
      }

      // 如果今天的更新时间都过了，取明天第一个
      if (!nextUpdate) {
        const tomorrow = new Date(today.getTime() + 86400000);
        const first = SCHEDULE_TIMES[0];
        nextUpdate = new Date(tomorrow.getTime() + first.hour * 3600000 + first.minute * 60000);
      }

      const diff = nextUpdate - now;
      const hours = Math.floor(diff / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);

      if (hours > 0) {
        this.countdownText = hours + this.t('countdownHour') + minutes + this.t('countdownMin');
      } else if (minutes > 0) {
        this.countdownText = minutes + this.t('countdownMin') + seconds + this.t('countdownSec');
      } else {
        this.countdownText = seconds + this.t('countdownSec');
      }
      this.countdownFullText = this.countdownText + this.t('countdownSuffix');
      if (this.lang === 'zh') {
        this.countdownText = this.countdownFullText;
      }
    },
    getDisplayLabel(source) {
      const map = this.lang === 'en' ? SOURCE_DISPLAY_MAP_EN : SOURCE_DISPLAY_MAP;
      return (map[source.id] || source).label;
    },
    getDisplayCategory(source) {
      const map = this.lang === 'en' ? SOURCE_DISPLAY_MAP_EN : SOURCE_DISPLAY_MAP;
      return (map[source.id] || source).category;
    },
    isDiscussion(item) {
      // 上游日报停止更新，暂时停用：
      // return item.source === 'Hacker News' || item.source === 'Linux.do';
      return item.source === 'Hacker News';
    },
    getOpenUrl(item) {
      if (item.source === 'Hacker News') {
        return (item.meta && item.meta.hn_url) || item.url;
      }
      return item.url;
    },
    formatDate(str) {
      if (!str) return '';
      const s = String(str).trim();
      // Unix timestamp（HN 使用，9-10 位纯数字）
      if (/^\d{9,10}$/.test(s)) {
        return new Date(Number(s) * 1000).toISOString().slice(0, 10);
      }
      // 已是 YYYY-MM-DD 格式，直接返回
      if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
      // ISO 8601 / RFC 2822 等，用 Date 解析后取前10位
      const d = new Date(s);
      if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
      // 尝试提取字符串中的 YYYY-MM-DD
      const m = s.match(/(\d{4}-\d{2}-\d{2})/);
      if (m) return m[1];
      return s;
    },
    getItemTags(item) {
      const tags = [];
      const meta = item.meta || {};
      const src = item.source || '';

      if (src === 'GitHub Trending Daily' || src === 'GitHub Trending Weekly') {
        if (meta.language)     tags.push({ label: meta.language, type: 'lang', dotColor: LANGUAGE_COLORS[meta.language] || '#888' });
        if (meta.stars)        tags.push({ label: '⭐ ' + meta.stars.toLocaleString(), type: 'stat' });
        if (meta.forks)        tags.push({ label: '🍴 ' + meta.forks.toLocaleString(), type: 'fork' });
        if (meta.stars_period) tags.push({ label: meta.stars_period, type: 'growth' });
      } else if (src === 'Hacker News') {
        if (meta.score != null)    tags.push({ label: '▲ ' + meta.score, type: 'stat' });
        if (meta.comments != null) tags.push({ label: '💬 ' + meta.comments + this.t('comments'), type: 'fork' });
      // 上游日报停止更新，暂时停用；保留标签逻辑供未来恢复。
      // } else if (src === 'Linux.do') {
      //   if (meta.section_title) tags.push({ label: meta.section_title, type: 'category' });
      //   if (meta.reply_count != null) tags.push({ label: '💬 ' + meta.reply_count + this.t('replies'), type: 'fork' });
      } else if (src === 'TLDR AI') {
        const cat = this.lang === 'en' ? item.category : TLDR_CATEGORY_MAP[item.category];
        if (cat) tags.push({ label: cat, type: 'category' });
      } else if (src === 'OpenAI' || src === 'Anthropic') {
        const ct = this.lang === 'en' ? meta.content_type : CONTENT_TYPE_MAP[meta.content_type];
        if (ct) tags.push({ label: ct, type: 'category' });
        if (item.published_at) tags.push({ label: this.formatDate(item.published_at), type: 'date' });
      } else if (src === 'InfoQ AI Development') {
        const cat = this.lang === 'en' ? item.category : INFOQ_CATEGORY_MAP[item.category];
        if (cat) tags.push({ label: cat, type: 'category' });
        if (item.published_at) tags.push({ label: this.formatDate(item.published_at), type: 'date' });
      }
      return tags;
    },
    async loadSources() {
      this.loading = true;
      this.errorMessage = '';
      try {
        const response = await fetch(`${API_PREFIX}/sources`);
        if (!response.ok) {
          throw new Error(`${this.t('sourceApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.sources = payload.sources || [];
        if (this.sources.length > 0) {
          await this.selectSource(this.sources[0].id);
        }
      } catch (error) {
        this.errorMessage = `${this.t('loadSourceErr')}${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    async selectSource(sourceId) {
      if (this.historyMode && this.selectedHistoryDate) {
        await this.loadHistorySource(sourceId);
        return;
      }
      this.activeSourceId = sourceId;
      this.loading = true;
      this.errorMessage = '';
      let shouldResetScroll = false;
      try {
        const response = await fetch(`${API_PREFIX}/sources/${sourceId}/latest`);
        if (!response.ok) {
          throw new Error(`${this.t('dataApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.items = payload.items || [];
        this.generatedAt = payload.generated_at || '';
        shouldResetScroll = true;
      } catch (error) {
        this.items = [];
        this.generatedAt = '';
        this.errorMessage = `${this.t('loadContentErr')}${error.message}`;
        shouldResetScroll = true;
      } finally {
        this.loading = false;
      }
      if (shouldResetScroll) {
        await this.$nextTick();
        this.resetFeedScroll();
      }
    }
  }
};
</script>

<style>
:root {
  --primary:       #0057FF;
  --primary-soft:  #EEF3FF;
  --bg:            #F2F5FA;
  --surface:       #FFFFFF;
  --border:        #E4E8F0;
  --text-1:        #0D1117;
  --text-2:        #4B5563;
  --text-3:        #9CA3AF;
  --brand-grad:    linear-gradient(135deg, #0057FF 0%, #7C3AED 100%);
  --body-pattern:  #C8D0DE;
  --topbar-bg:     rgba(255, 255, 255, 0.92);
  --preference-bg: #FBFCFF;
  --control-bg:    #F1F3F8;
  --control-hover: #F7F8FB;
  --hover-bg:      #F6F9FF;
  --accent-border: #C7D9FF;
  --active-muted:  #6B9BFF;
  --drawer-mask:   rgba(15, 23, 42, 0.22);
  --drawer-shadow: -18px 0 40px rgba(15, 23, 42, 0.16);
  --history-row-bg:#F8FAFC;
  --error-border:  #FECACA;
  --error-text:    #B91C1C;
  --error-bg:      #FEF2F2;
  --tag-lang-bg:   #F3F4F6;
  --tag-lang-text: #374151;
  --tag-lang-bd:   #E5E7EB;
  --tag-stat-bg:   #FFFBEB;
  --tag-stat-text: #92400E;
  --tag-stat-bd:   #FDE68A;
  --tag-fork-bg:   #F0F4FF;
  --tag-fork-text: #3B5BDB;
  --tag-fork-bd:   #C5D0FA;
  --tag-growth-bg: #F0FDF4;
  --tag-growth-text:#166534;
  --tag-growth-bd: #BBF7D0;
  --tag-date-bg:   #F9FAFB;
  --tag-date-text: #6B7280;
  --tag-date-bd:   #E5E7EB;
  --skeleton-grad: linear-gradient(90deg, #EAECF0 25%, #F5F6F8 50%, #EAECF0 75%);
  --footer-hover:  rgba(15, 23, 42, 0.05);
  --radius-card:   10px;
  --shadow-card:   0 1px 3px rgba(0, 0, 0, .06), 0 4px 12px rgba(0, 0, 0, .04);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  color: var(--text-1);
  background: #F2F5FA;
  font-family: 'DM Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
}

a {
  color: inherit;
  text-decoration: none;
}

.app-shell {
  min-height: 100vh;
  color: var(--text-1);
  background: var(--bg);
  background-image: radial-gradient(circle, var(--body-pattern) 1px, transparent 1px);
  background-size: 28px 28px;
  transition: background-color 180ms ease, color 180ms ease;
}

.theme-dark {
  color-scheme: dark;
  --primary:       #7AA2FF;
  --primary-soft:  rgba(122, 162, 255, 0.14);
  --bg:            #0D1117;
  --surface:       #151B23;
  --border:        #30363D;
  --text-1:        #F0F6FC;
  --text-2:        #C9D1D9;
  --text-3:        #8B949E;
  --brand-grad:    linear-gradient(135deg, #2F81F7 0%, #A371F7 100%);
  --body-pattern:  rgba(139, 148, 158, 0.18);
  --topbar-bg:     rgba(13, 17, 23, 0.9);
  --preference-bg: #111820;
  --control-bg:    #21262D;
  --control-hover: #262C36;
  --hover-bg:      rgba(122, 162, 255, 0.08);
  --accent-border: rgba(122, 162, 255, 0.42);
  --active-muted:  #9DB8FF;
  --drawer-mask:   rgba(0, 0, 0, 0.5);
  --drawer-shadow: -18px 0 42px rgba(0, 0, 0, 0.42);
  --history-row-bg:#111820;
  --error-border:  rgba(248, 113, 113, 0.38);
  --error-text:    #FCA5A5;
  --error-bg:      rgba(127, 29, 29, 0.18);
  --tag-lang-bg:   #21262D;
  --tag-lang-text: #C9D1D9;
  --tag-lang-bd:   #30363D;
  --tag-stat-bg:   rgba(180, 83, 9, 0.18);
  --tag-stat-text: #FCD34D;
  --tag-stat-bd:   rgba(245, 158, 11, 0.32);
  --tag-fork-bg:   rgba(59, 130, 246, 0.16);
  --tag-fork-text: #93C5FD;
  --tag-fork-bd:   rgba(96, 165, 250, 0.32);
  --tag-growth-bg: rgba(22, 101, 52, 0.18);
  --tag-growth-text:#86EFAC;
  --tag-growth-bd: rgba(74, 222, 128, 0.28);
  --tag-date-bg:   #161B22;
  --tag-date-text: #AAB4C0;
  --tag-date-bd:   #30363D;
  --skeleton-grad: linear-gradient(90deg, #1C2128 25%, #252B34 50%, #1C2128 75%);
  --footer-hover:  rgba(201, 209, 217, 0.08);
  --shadow-card:   0 1px 3px rgba(0, 0, 0, .24), 0 10px 28px rgba(0, 0, 0, .24);
}

/* ── Topbar ───────────────────────────────── */

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 32px;
  height: 64px;
  background: var(--topbar-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark-wrapper {
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.brand-mark-ring {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  background: var(--brand-grad);
  opacity: 0.3;
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.15); opacity: 0.1; }
}

.brand-mark {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--brand-grad);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: grid;
  place-items: center;
  letter-spacing: 0.5px;
}

.brand-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.3px;
  color: var(--text-1);
  font-family: 'Bricolage Grotesque', 'DM Sans', sans-serif;
}

.brand-text p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--text-3);
  letter-spacing: 0.2px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.preference-group,
.utility-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.preference-group {
  padding: 3px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--preference-bg);
}

.history-button {
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-3);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  padding: 5px 8px;
  transition: color 150ms ease, background 150ms ease;
}

.history-button:hover,
.history-button:focus-visible {
  background: var(--control-bg);
  color: var(--primary);
  outline: none;
}

.gh-link {
  display: flex;
  align-items: center;
  color: var(--text-3);
  transition: color 150ms ease;
}

.gh-link:hover {
  color: var(--text-1);
}

.theme-toggle {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: border-color 150ms ease, color 150ms ease, background 150ms ease;
}

.preference-group .theme-toggle {
  border-color: transparent;
  background: var(--primary-soft);
  color: var(--primary);
}

.theme-toggle:hover,
.theme-toggle:focus-visible {
  border-color: var(--accent-border);
  background: var(--primary-soft);
  color: var(--primary);
  outline: none;
}

.update-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 76px;
  padding: 5px 12px;
  border-radius: 20px;
  background: var(--control-bg);
  color: var(--text-2);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.update-chip-icon,
.update-chip-text {
  line-height: 1;
}

/* ── Layout ───────────────────────────────── */

.layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 24px 56px;
}

/* ── Source panel ─────────────────────────── */

.source-panel {
  position: sticky;
  top: 84px;
  align-self: start;
  padding: 6px;
  border-radius: var(--radius-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.source-tab {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 52px;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 10px 12px 10px 16px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text-1);
  cursor: pointer;
  text-align: left;
  transition: background 150ms ease;
  overflow: hidden;
}

.source-tab + .source-tab {
  margin-top: 2px;
}

.source-tab::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: transparent;
  transition: background 150ms ease;
}

.source-tab span {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}

.source-tab small {
  margin-top: 3px;
  color: var(--text-3);
  font-size: 11px;
  font-weight: 400;
}

.source-tab.active {
  background: var(--primary-soft);
  color: var(--primary);
}

.source-tab.active small {
  color: var(--active-muted);
}

.source-tab.active::before {
  background: var(--primary);
}

.source-tab:hover:not(.active) {
  background: var(--control-hover);
}

/* ── Feed panel ───────────────────────────── */

.feed-panel {
  min-width: 0;
  border-radius: var(--radius-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.feed-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px 18px;
  border-bottom: 1px solid var(--border);
}

.feed-toolbar h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--text-1);
  font-family: 'Bricolage Grotesque', 'DM Sans', sans-serif;
}

.feed-subtitle {
  margin: 6px 0 0;
  color: var(--text-3);
  font-size: 13px;
  line-height: 1.5;
}

.back-today-button {
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 11px;
  transition: border-color 150ms ease, color 150ms ease, background 150ms ease;
}

.back-today-button:hover,
.back-today-button:focus-visible {
  border-color: var(--accent-border);
  background: var(--primary-soft);
  color: var(--primary);
  outline: none;
}

/* ── History drawer ───────────────────────── */

.history-drawer-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: none;
  background: var(--drawer-mask);
}

.history-drawer-mask.open {
  display: block;
}

.history-drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: min(440px, 100vw);
  height: 100%;
  overflow-y: auto;
  background: var(--surface);
  box-shadow: var(--drawer-shadow);
}

.history-drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px;
  border-bottom: 1px solid var(--border);
}

.history-drawer-head h2 {
  margin: 0;
  color: var(--text-1);
  font-size: 20px;
  line-height: 1.3;
}

.history-drawer-head p {
  margin: 6px 0 0;
  color: var(--text-3);
  font-size: 13px;
  line-height: 1.6;
}

.history-drawer-close {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.history-drawer-close:hover,
.history-drawer-close:focus-visible {
  background: var(--control-hover);
  outline: none;
}

.history-date-list {
  padding: 14px;
}

.history-date-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  width: 100%;
  min-height: 62px;
  margin-bottom: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--history-row-bg);
  color: var(--text-1);
  cursor: pointer;
  text-align: left;
  transition: border-color 150ms ease, background 150ms ease;
}

.history-date-row:hover:not(:disabled) {
  border-color: var(--accent-border);
  background: var(--hover-bg);
}

.history-date-row.active {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.history-date-row.disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.history-date-row strong {
  font-size: 15px;
  line-height: 1.2;
}

.history-date-row span {
  min-width: 0;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.4;
}

.history-drawer-state {
  margin: 18px 14px;
  padding: 22px;
  border: 1px dashed var(--border);
  border-radius: 8px;
  color: var(--text-3);
  text-align: center;
  font-size: 14px;
}

.history-drawer-state.error {
  border-color: var(--error-border);
  color: var(--error-text);
  background: var(--error-bg);
}

/* ── Feed item ────────────────────────────── */

.feed-item {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  padding: 22px 24px;
  border-bottom: 1px solid var(--border);
  transition: background 150ms ease;
}

.feed-item:last-child {
  border-bottom: 0;
}

.feed-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
  transition: background 150ms ease;
}

.feed-item:hover {
  background: var(--hover-bg);
}

.feed-item:hover::before {
  background: var(--primary);
}

.item-title {
  display: inline;
  color: var(--text-1);
  font-size: 16px;
  line-height: 1.5;
  font-weight: 600;
  letter-spacing: -0.1px;
  transition: color 150ms ease;
}

.item-title:hover {
  color: var(--primary);
}

.item-summary {
  margin: 8px 0 0;
  color: var(--text-2);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-line;
}

/* ── Item tags ────────────────────────────── */

.item-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0 0;
}

.item-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.7;
  white-space: nowrap;
  border: 1px solid transparent;
}

/* 语言 tag — 灰色胶囊 + 彩色圆点 */
.item-tag--lang {
  background: var(--tag-lang-bg);
  color: var(--tag-lang-text);
  border-color: var(--tag-lang-bd);
}

/* 圆点 */
.lang-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Stars — 暖金 */
.item-tag--stat {
  background: var(--tag-stat-bg);
  color: var(--tag-stat-text);
  border-color: var(--tag-stat-bd);
}

/* Forks / 评论 — 蓝灰 */
.item-tag--fork {
  background: var(--tag-fork-bg);
  color: var(--tag-fork-text);
  border-color: var(--tag-fork-bd);
}

/* Stars today — 绿色 */
.item-tag--growth {
  background: var(--tag-growth-bg);
  color: var(--tag-growth-text);
  border-color: var(--tag-growth-bd);
}

/* 分类 — 主色蓝 */
.item-tag--category {
  background: var(--primary-soft);
  color: var(--primary);
  border-color: var(--accent-border);
}

/* 日期 — 中性灰 */
.item-tag--date {
  background: var(--tag-date-bg);
  color: var(--tag-date-text);
  border-color: var(--tag-date-bd);
}

.open-link {
  align-self: start;
  flex-shrink: 0;
  color: var(--primary);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  padding: 2px 0;
  transition: opacity 150ms ease;
}

.open-link:hover {
  opacity: 0.75;
}

/* ── Podcast ─────────────────────────────── */

.podcast-episode {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 24px;
  padding: 24px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(90deg, rgba(0, 87, 255, 0.08), rgba(16, 185, 129, 0.08));
}

.podcast-episode-main {
  min-width: 0;
}

.podcast-kicker {
  display: inline-flex;
  margin-bottom: 10px;
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
}

.podcast-episode h3 {
  margin: 0;
  color: var(--text-1);
  font-size: 24px;
  line-height: 1.35;
  letter-spacing: 0;
}

.podcast-summary {
  margin: 10px 0 0;
  color: var(--text-2);
  font-size: 14px;
  line-height: 1.7;
}

.podcast-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.podcast-meta-row span {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 9px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
  color: var(--text-3);
  font-size: 12px;
}

.podcast-player {
  width: min(560px, 100%);
  margin-top: 16px;
}

.podcast-chapters {
  align-self: start;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
}

.podcast-chapters h4 {
  margin: 0 0 12px;
  color: var(--text-1);
  font-size: 14px;
}

.podcast-chapter {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 8px;
  padding: 9px 0;
  border-top: 1px solid var(--border);
}

.podcast-chapter:first-of-type {
  border-top: 0;
  padding-top: 0;
}

.podcast-chapter span {
  color: var(--primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  font-weight: 700;
}

.podcast-chapter strong {
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.45;
}

/* ── Skeleton ─────────────────────────────── */

@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position:  600px 0; }
}

.skeleton-card {
  padding: 22px 24px;
  border-bottom: 1px solid var(--border);
}

.skeleton-card:last-child {
  border-bottom: 0;
}

.skeleton-line {
  border-radius: 6px;
  background: var(--skeleton-grad);
  background-size: 600px 100%;
  animation: shimmer 1.4s infinite linear;
}

.skeleton-line.title {
  height: 20px;
  width: 65%;
  margin-bottom: 14px;
}

.skeleton-line.body {
  height: 13px;
  width: 100%;
  margin-bottom: 8px;
}

.skeleton-line.short {
  width: 50%;
  margin-bottom: 0;
}

/* ── State box ────────────────────────────── */

.state-box {
  margin: 32px 24px;
  padding: 32px;
  border: 1px dashed var(--border);
  border-radius: 8px;
  color: var(--text-3);
  text-align: center;
  font-size: 14px;
}

.state-box.error {
  border-color: var(--error-border);
  color: var(--error-text);
  background: var(--error-bg);
}

/* ── Mobile ───────────────────────────────── */

@media (max-width: 860px) {
  .topbar {
    position: static;
    height: auto;
    flex-wrap: wrap;
    padding: 12px 16px;
    gap: 8px;
  }

  .update-chip {
    font-size: 11px;
    padding: 4px 10px;
  }

  .update-chip--compact-mobile {
    width: 32px;
    min-width: 32px;
    height: 32px;
    gap: 0;
    padding: 0;
    font-size: 14px;
  }

  .update-chip--compact-mobile .update-chip-text {
    display: none;
  }

  .topbar-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
  }

  .history-button {
    font-size: 12px;
    padding: 4px 6px;
  }

  .layout {
    display: block;
    padding: 12px 16px 40px;
  }

  .source-panel {
    position: static;
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    padding: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .source-tab {
    width: 140px;
    flex: 0 0 140px;
    min-height: 48px;
    border: 1px solid var(--border);
  }

  .source-tab + .source-tab {
    margin-top: 0;
  }

  .source-tab::before {
    display: none;
  }

  .feed-toolbar,
  .feed-item {
    padding: 16px;
  }

  .feed-toolbar {
    display: block;
  }

  .feed-item {
    display: block;
  }

  .podcast-episode {
    grid-template-columns: 1fr;
  }

  .podcast-episode {
    padding: 16px;
  }

  .back-today-button {
    margin-top: 12px;
  }

  .history-drawer {
    width: 100vw;
  }

  .open-link {
    display: inline-block;
    margin-top: 10px;
  }
}

/* ── Footer ──────────────────────────────── */
.site-footer {
  text-align: center;
  padding: 24px 0;
  color: var(--text-3);
  font-size: 13px;
  border-top: 1px solid var(--border);
  margin-top: 32px;
}

.footer-easter-egg {
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 150ms ease, background 150ms ease;
}

.footer-easter-egg:hover,
.footer-easter-egg:focus-visible {
  color: var(--text-1);
  background: var(--footer-hover);
  outline: none;
}

/* ── Language Switch ─────────────────────── */
.lang-switch {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.lang-switch button {
  border: none;
  background: transparent;
  color: var(--text-3);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: color 150ms ease, background 150ms ease;
}

.lang-switch button:hover {
  color: var(--text-1);
}

.lang-switch button.active {
  color: var(--primary);
  font-weight: 600;
}

.lang-sep {
  color: var(--text-3);
  font-size: 13px;
  user-select: none;
}
</style>
