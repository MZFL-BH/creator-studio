const SCENE_SUBS = {
  scene1: [
    { start: 0.00, end: 3.58, html: '你装的 <span class="hl">AI 一键生成 PPT</span>，真的该<span class="hl">全删了</span>！' },
    { start: 4.08, end: 12.42, html: '很多人以为装了神器就能一键交差，结果到了周会，不是<span class="hl">母版被乱改</span>，就是数据被<span class="hl">偷偷造假</span>！' },
    { start: 13.02, end: 19.50, html: '今天不吹不黑，拿大厂真实母版实测给你看，顺便只留下真正能保命的生产级方案。' }
  ],
  scene2: [
    { start: 0.00, end: 9.18, html: '第一关，<span class="hl">格式关</span>。领导和客户要的从来不是商城模版，而是公司的<span class="hl">统一规范母版</span>！' },
    { start: 9.60, end: 15.88, html: '结果文件一丢进去，直接弹窗警告：<span class="hl">母版无法识别</span>，强制替换为商城风！' },
    { start: 16.40, end: 24.60, html: '甚至有些工具在线看着炫，一导出本地 PPTX，Logo 变形，文本框碎成三十多个！' },
    { start: 25.10, end: 29.00, html: '调格式花的时间，比你自己手搓<span class="hl">还要慢一倍</span>！' }
  ],
  scene3: [
    { start: 0.00, end: 4.96, html: '排版乱就算了，第二关更要命：AI 在背地里偷偷给你<span class="hl">造假</span>！' },
    { start: 5.40, end: 11.70, html: '我原稿清清楚楚写着：完成率 <span class="hl">86.4%</span>，面临核心技术人员短缺风险。' },
    { start: 12.20, end: 19.00, html: '结果 AI 为了句式工整，大笔一挥写成：超额达成近 <span class="hl">90%</span>，全方位拉通闭环！' },
    { start: 19.50, end: 23.40, html: '甚至凭空给竞对编造了根本不存在的市场下滑数据！' },
    { start: 23.90, end: 28.60, html: '周会上领导问你这数据哪来的，你敢说是 AI 编的吗？' },
    { start: 29.20, end: 32.50, html: '这不是提效，这是在工位上<span class="hl">埋雷</span>！' }
  ],
  scene4: [
    { start: 0.00, end: 1.80, html: '为什么做 PPT 这么痛苦？' },
    { start: 2.10, end: 8.10, html: '因为市面上 90% 的一键 PPT，本质上就是个排版玩具，根本不懂职场规则。' },
    { start: 8.50, end: 15.70, html: '真正能交差的职场 PPT 就两点：第一，<span class="hl">母版必须是公司的</span>；第二，<span class="hl">数据绝对不能撒谎</span>！' },
    { start: 16.30, end: 23.00, html: '那到底有没有真正能打的解法？记住这套<span class="hl">大模型骨架加原生母版两阶段法</span>。' }
  ],
  scene5: [
    { start: 0.00, end: 9.70, html: '打工人保命第一步：让大模型只当<span class="hl">架构师</span>，只提炼 Markdown 逻辑大纲，强约束严禁杜撰数据。' },
    { start: 10.00, end: 23.00, html: '第二步：回归本地 Office 生态，通过母版插件或脚本一键灌入原生模板，字体Logo一动不动，<span class="hl">5分钟稳稳交差</span>！' }
  ],
  scene6: [
    { start: 0.00, end: 4.36, html: '我是 Ethan，专注拿真机击穿营销滤镜的实测工程师。' },
    { start: 4.90, end: 12.80, html: '这次用到的《公司 PPT 母版规范排查清单》和《高压周报防翻车 Prompt 模板》，已经全部脱敏打包好了。' },
    { start: 13.30, end: 21.50, html: '在评论区回复 <span class="hl">PPT</span>，原件直接发你对照避坑！赶紧点赞收藏，下次汇报前拿出来自保！' }
  ]
};

window.renderSubtitle = function(sceneId, t) {
  let subContainer = document.getElementById('sceneSubtitle');
  if (!subContainer) {
    const layer = document.createElement('div');
    layer.style.position = 'absolute';
    layer.style.bottom = '160px';
    layer.style.left = '60px';
    layer.style.right = '60px';
    layer.style.textAlign = 'center';
    layer.style.pointerEvents = 'none';
    layer.style.zIndex = '999';
    
    subContainer = document.createElement('div');
    subContainer.id = 'sceneSubtitle';
    subContainer.style.display = 'inline-block';
    subContainer.style.background = 'rgba(15, 23, 42, 0.88)';
    subContainer.style.backdropFilter = 'blur(12px)';
    subContainer.style.color = '#ffffff';
    subContainer.style.fontSize = '40px';
    subContainer.style.fontWeight = '800';
    subContainer.style.padding = '18px 36px';
    subContainer.style.borderRadius = '24px';
    subContainer.style.border = '2px solid rgba(255, 255, 255, 0.2)';
    subContainer.style.letterSpacing = '1px';
    subContainer.style.boxShadow = '0 15px 40px rgba(0,0,0,0.35)';
    subContainer.style.lineHeight = '1.4';
    subContainer.style.transition = 'all 0.2s';
    
    layer.appendChild(subContainer);
    document.body.appendChild(layer);

    // Add highlight style
    const style = document.createElement('style');
    style.innerHTML = `
      #sceneSubtitle .hl {
        color: #facc15 !important;
        text-shadow: 0 0 16px rgba(250, 204, 21, 0.8);
      }
    `;
    document.head.appendChild(style);
  }

  const list = SCENE_SUBS[sceneId] || [];
  const cue = list.find(item => t >= item.start && t <= item.end);
  if (cue) {
    subContainer.style.opacity = '1';
    subContainer.innerHTML = cue.html;
  } else {
    subContainer.style.opacity = '0';
  }
};
