(() => {
  const bubble = document.getElementById('assistantBubble');
  const panel = document.getElementById('assistantPanel');
  if (!bubble || !panel) return;

  const closeBtn = document.getElementById('assistantClose');
  const messagesEl = document.getElementById('assistantMessages');
  const input = document.getElementById('assistantInput');
  const sendBtn = document.getElementById('assistantSend');
  const modeSelect = document.getElementById('assistantMode');
  const activityEl = document.getElementById('assistantActivity');
  const activityList = document.getElementById('assistantActivityList');
  const activityToggle = document.getElementById('assistantActivityToggle');
  const convoSelect = document.getElementById('assistantConversationSelect');
  const convoNewBtn = document.getElementById('assistantConversationNew');
  const convoRenameBtn = document.getElementById('assistantConversationRename');
  const convoRenameInline = document.getElementById('assistantConversationRenameInline');
  const convoRenameInput = document.getElementById('assistantConversationRenameInput');
  const convoRenameSave = document.getElementById('assistantConversationRenameSave');
  const convoRenameCancel = document.getElementById('assistantConversationRenameCancel');

  const defaultMode = panel.dataset.defaultMode || 'approval';
  modeSelect.value = defaultMode;

  let historyLoaded = false;
  let conversationsLoaded = false;
  let currentConversationId = null;

  const scrollToBottom = () => {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  };

  const addMessage = (role, content) => {
    const msg = document.createElement('div');
    msg.className = `assistant-message ${role}`;
    msg.textContent = content;
    messagesEl.appendChild(msg);
    scrollToBottom();
    return msg;
  };

  const setLoading = (msgEl, isLoading) => {
    if (!msgEl) return;
    if (isLoading) {
      msgEl.dataset.loading = 'true';
      msgEl.classList.add('assistant-loading');
      msgEl.innerHTML = '<div class="spinner-grow" role="status"><span class="visually-hidden">Loading...</span></div>';
    } else {
      msgEl.dataset.loading = 'false';
      msgEl.classList.remove('assistant-loading');
    }
  };

  const addMuted = (content) => {
    const msg = document.createElement('div');
    msg.className = 'assistant-muted';
    msg.textContent = content;
    messagesEl.appendChild(msg);
    scrollToBottom();
    return msg;
  };

  const addMutedLoading = (content) => {
    const msg = document.createElement('div');
    msg.className = 'assistant-muted assistant-muted-loading';
    msg.innerHTML = `<div class="spinner-grow" role="status"><span class="visually-hidden">Loading...</span></div><span>${content}</span>`;
    messagesEl.appendChild(msg);
    scrollToBottom();
    return msg;
  };

  const addActivity = (result) => {
    if (!activityList) return;
    const item = document.createElement('div');
    item.className = `assistant-activity-item${result.status === 'error' ? ' error' : ''}`;
    item.textContent = result.message || 'Action completed.';
    activityList.prepend(item);
  };

  const renderActionCard = (action, messageId, actionIndex) => {
    const card = document.createElement('div');
    card.className = 'assistant-action';
    const title = document.createElement('div');
    title.className = 'assistant-action-title';
    title.textContent = action.title || action.type || 'Proposed action';
    card.appendChild(title);

    if (action.summary) {
      const summary = document.createElement('div');
      summary.textContent = action.summary;
      card.appendChild(summary);
    }

    const buttons = document.createElement('div');
    buttons.className = 'assistant-action-buttons';

    const approveBtn = document.createElement('button');
    approveBtn.className = 'btn btn-sm btn-primary';
    approveBtn.textContent = 'Confirm';
    approveBtn.addEventListener('click', async () => {
      approveBtn.disabled = true;
      approveBtn.classList.add('assistant-action-working');
      approveBtn.innerHTML = '<span class="spinner-grow" role="status"></span> Working';
      const resp = await fetch('/assistant/actions/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, action_index: actionIndex })
      });
      const data = await resp.json();
      if (resp.ok) {
        addMessage('assistant', data.message || 'Action applied.');
        addActivity(data.result || { message: data.message || 'Action applied.' });
        card.remove();
      } else {
        addMessage('assistant', data.error || 'Unable to apply action.');
        approveBtn.disabled = false;
        approveBtn.classList.remove('assistant-action-working');
        approveBtn.textContent = 'Confirm';
      }
    });

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-sm btn-outline-secondary';
    cancelBtn.textContent = 'Dismiss';
    cancelBtn.addEventListener('click', async () => {
      await fetch('/assistant/actions/dismiss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, action_index: actionIndex })
      });
      card.remove();
    });

    buttons.appendChild(approveBtn);
    buttons.appendChild(cancelBtn);
    card.appendChild(buttons);

    messagesEl.appendChild(card);
    scrollToBottom();
  };

  const loadHistory = async () => {
    if (historyLoaded) return;
    historyLoaded = true;
    const resp = await fetch('/assistant/history');
    if (!resp.ok) return;
    const data = await resp.json();
    currentConversationId = data.conversation_id || currentConversationId;
    if (data.mode) {
      modeSelect.value = data.mode;
    }
    if (activityList) activityList.innerHTML = '';
    (data.messages || []).forEach((msg) => {
      addMessage(msg.role, msg.content);
      if (msg.actions && msg.actions.length && modeSelect.value === 'approval' && (!msg.action_results || !msg.action_results.length)) {
        msg.actions.forEach((action, idx) => renderActionCard(action, msg.id, idx));
      }
      if (msg.action_results && msg.action_results.length) {
        msg.action_results.forEach((result) => {
          addMessage('assistant', result.message || 'Action completed.');
          addActivity(result);
        });
      }
    });
  };

  const loadConversations = async () => {
    if (conversationsLoaded) return;
    conversationsLoaded = true;
    if (!convoSelect) return;
    const resp = await fetch('/assistant/conversations');
    if (!resp.ok) return;
    const data = await resp.json();
    currentConversationId = data.current_id || currentConversationId;
    convoSelect.innerHTML = '';
    (data.conversations || []).forEach((convo) => {
      const opt = document.createElement('option');
      opt.value = convo.id;
      opt.textContent = convo.title || 'Chat';
      if (convo.id === currentConversationId) {
        opt.selected = true;
      }
      convoSelect.appendChild(opt);
    });
  };

  const resetChatView = () => {
    messagesEl.innerHTML = '';
    if (activityList) activityList.innerHTML = '';
    historyLoaded = false;
  };

  const togglePanel = async () => {
    panel.classList.toggle('open');
    const isOpen = panel.classList.contains('open');
    panel.setAttribute('aria-hidden', (!isOpen).toString());
    if (isOpen) {
      await loadConversations();
      await loadHistory();
      input.focus();
      scrollToBottom();
    }
  };

  bubble.addEventListener('click', togglePanel);
  closeBtn.addEventListener('click', togglePanel);

  if (activityToggle && activityEl) {
    activityToggle.addEventListener('click', () => {
      const list = activityEl.querySelector('.assistant-activity-list');
      if (!list) return;
      const isHidden = list.style.display === 'none';
      list.style.display = isHidden ? '' : 'none';
      activityToggle.textContent = isHidden ? 'Hide' : 'Show';
      activityToggle.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
    });
  }

  modeSelect.addEventListener('change', async () => {
    const mode = modeSelect.value;
    await fetch('/assistant/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    });
    addMuted(`Mode set to ${mode === 'auto' ? 'Auto' : 'Approval required'}.`);
  });

  if (convoSelect) {
    convoSelect.addEventListener('change', async () => {
      const convoId = convoSelect.value;
      if (!convoId) return;
      await fetch('/assistant/conversations/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: convoId })
      });
      currentConversationId = convoId;
      resetChatView();
      await loadHistory();
    });
  }

  if (convoNewBtn) {
    convoNewBtn.addEventListener('click', async () => {
      const resp = await fetch('/assistant/conversations/new', { method: 'POST' });
      if (!resp.ok) return;
      const data = await resp.json();
      currentConversationId = data.conversation_id;
      conversationsLoaded = false;
      resetChatView();
      await loadConversations();
      await loadHistory();
    });
  }

  if (convoRenameBtn) {
    convoRenameBtn.addEventListener('click', () => {
      if (!currentConversationId || !convoRenameInline || !convoRenameInput) return;
      convoRenameInline.hidden = false;
      convoRenameInput.value = convoSelect?.selectedOptions?.[0]?.textContent || '';
      convoRenameInput.focus();
    });
  }

  if (convoRenameCancel) {
    convoRenameCancel.addEventListener('click', () => {
      if (convoRenameInline) convoRenameInline.hidden = true;
    });
  }

  if (convoRenameSave) {
    convoRenameSave.addEventListener('click', async () => {
      if (!currentConversationId || !convoRenameInput) return;
      const title = convoRenameInput.value.trim();
      if (!title) return;
      const resp = await fetch('/assistant/conversations/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: currentConversationId, title })
      });
      if (!resp.ok) return;
      if (convoRenameInline) convoRenameInline.hidden = true;
      conversationsLoaded = false;
      await loadConversations();
    });
  }

  const sendMessage = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage('user', text);
    const assistantMsgEl = addMessage('assistant', '');
    setLoading(assistantMsgEl, true);

    const resp = await fetch('/assistant/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, mode: modeSelect.value })
    });

    if (!resp.ok || !resp.body) {
      setLoading(assistantMsgEl, false);
      assistantMsgEl.textContent = 'Unable to reach assistant.';
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let parts = buffer.split('\n\n');
      buffer = parts.pop();
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith('data:')) continue;
        const payload = line.replace('data:', '').trim();
        if (!payload) continue;
        let event;
        try {
          event = JSON.parse(payload);
        } catch (e) {
          continue;
        }
        if (event.type === 'delta') {
          if (assistantMsgEl.dataset.loading === 'true') {
            setLoading(assistantMsgEl, false);
            assistantMsgEl.textContent = '';
          }
          assistantMsgEl.textContent += event.content;
          scrollToBottom();
        }
        if (event.type === 'actions') {
          if (event.actions && event.actions.length && modeSelect.value === 'approval') {
            event.actions.forEach((action, idx) => renderActionCard(action, event.message_id, idx));
          }
          let autoStatusEl = null;
          if (event.actions && event.actions.length && modeSelect.value === 'auto') {
            autoStatusEl = addMutedLoading('Applying action...');
          }
          if (event.action_results && event.action_results.length) {
            event.action_results.forEach((result) => {
              addMessage('assistant', result.message || 'Action completed.');
              addActivity(result);
            });
            if (autoStatusEl) autoStatusEl.remove();
          }
        }
        if (event.type === 'error') {
          setLoading(assistantMsgEl, false);
          assistantMsgEl.textContent = event.message || 'Assistant error.';
        }
      }
    }
  };

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });
})();
