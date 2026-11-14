document.addEventListener("DOMContentLoaded", function () {
    const app = document.getElementById("conversationApp");
    if (!app) return;

    const messageList = document.getElementById("messageList");
    const presenceDot = document.getElementById("presenceDot");
    const presenceStatus = document.getElementById("presenceStatus");
    const connectionStatus = document.getElementById("connectionStatus");
    const form = document.getElementById("messageForm");
    const input = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const notificationButton = document.getElementById("enableNotifications");
    const currentUserId = Number(app.dataset.currentUserId);
    const peerId = Number(app.dataset.peerId);
    const peerName = app.dataset.peerName;
    const canSend = app.dataset.canSend === "true";
    let socket;
    let retryCount = 0;
    let reconnectTimer;
    let presenceTimer;
    let closing = false;

    function setPresence(online) {
        presenceDot.classList.toggle("online", online);
        presenceStatus.textContent = online ? "En ligne" : "Hors ligne";
    }

    function appendMessage(message) {
        const emptyState = document.getElementById("emptyMessages");
        if (emptyState) emptyState.remove();

        const row = document.createElement("article");
        row.className =
            "message-row" + (message.sender_id === currentUserId ? " mine" : "");
        row.dataset.messageId = String(message.id);

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        const author = document.createElement("div");
        author.className = "small fw-semibold";
        author.textContent = message.sender_name;

        const text = document.createElement("div");
        text.className = "message-text";
        text.textContent = message.text;

        const meta = document.createElement("div");
        meta.className = "message-meta";
        const sentAt = new Date(message.sent_at);
        meta.append(document.createTextNode(
            Number.isNaN(sentAt.getTime())
                ? ""
                : sentAt.toLocaleString("fr-FR", {
                    dateStyle: "short",
                    timeStyle: "short"
                })
        ));

        if (message.sender_id === currentUserId) {
            meta.append(document.createTextNode(" · "));
            const readStatus = document.createElement("span");
            readStatus.className = "read-status";
            readStatus.textContent = message.read_at ? "Lu" : "Envoyé";
            meta.append(readStatus);
        }

        bubble.append(author, text, meta);
        row.appendChild(bubble);
        messageList.appendChild(row);
        messageList.scrollTop = messageList.scrollHeight;
        return row;
    }

    function showNotification(message) {
        if (
            document.visibilityState === "visible" ||
            !("Notification" in window) ||
            Notification.permission !== "granted"
        ) return;

        new Notification("Nouveau message TOUKPEDIO", {
            body: message.text,
            tag: "toukpedio-conversation-" + app.dataset.conversationId
        });
    }

    function handleSocketMessage(event) {
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            return;
        }

        if (data.type === "message") {
            const row = appendMessage(data);
            if (data.sender_id !== currentUserId) {
                showNotification(data);
                if (document.visibilityState === "visible" && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        action: "mark_read",
                        message_ids: [data.id]
                    }));
                }
            }
        } else if (data.type === "read") {
            data.message_ids.forEach(function (messageId) {
                const row = messageList.querySelector(
                    '[data-message-id="' + messageId + '"]'
                );
                const status = row && row.querySelector(".read-status");
                if (status) status.textContent = "Lu";
            });
        } else if (data.type === "presence" && data.user_id === peerId) {
            clearTimeout(presenceTimer);
            setPresence(data.online);
        } else if (data.type === "error") {
            connectionStatus.textContent = data.message;
        }
    }

    function connect() {
        connectionStatus.textContent = "Connexion en cours…";
        socket = new WebSocket(app.dataset.websocketUrl);

        socket.addEventListener("open", function () {
            retryCount = 0;
            if (connectionStatus) {
                connectionStatus.textContent = "Connecté";
            }
            if (sendButton) {
                sendButton.disabled = !canSend;
            }
            setPresence(false);
            socket.send(JSON.stringify({ action: "presence_check" }));
            const unreadIds = Array.from(
                messageList.querySelectorAll(".message-row:not(.mine)")
            ).map(function (row) {
                return Number(row.dataset.messageId);
            });
            if (unreadIds.length) {
                socket.send(JSON.stringify({
                    action: "mark_read",
                    message_ids: unreadIds
                }));
            }
            presenceTimer = setTimeout(function () {
                setPresence(false);
            }, 1200);
        });

        socket.addEventListener("message", handleSocketMessage);
        socket.addEventListener("close", function () {
            if (sendButton) {
                sendButton.disabled = true;
            }
            if (connectionStatus) {
                connectionStatus.textContent = "Déconnecté. Reconnexion…";
            }
            setPresence(false);
            if (!closing && retryCount < 8) {
                const delay = Math.min(1000 * (2 ** retryCount), 15000);
                retryCount += 1;
                reconnectTimer = setTimeout(connect, delay);
            } else {
                if (connectionStatus) {
                    connectionStatus.textContent =
                        "Connexion interrompue. Rechargez la page pour réessayer.";
                }
            }
        });

        socket.addEventListener("error", function () {
            if (connectionStatus) {
                connectionStatus.textContent = "Erreur de connexion en temps réel.";
            }
        });
    }

    if (form && input) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            const text = input.value.trim();
            if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;

            socket.send(JSON.stringify({
                action: "send_message",
                text: text
            }));
            input.value = "";
            input.focus();
        });
    }

    if (notificationButton) {
        if (!("Notification" in window)) {
            notificationButton.hidden = true;
        } else if (Notification.permission === "granted") {
            notificationButton.textContent = "Notifications activées";
            notificationButton.disabled = true;
        }

        notificationButton.addEventListener("click", async function () {
            if (!("Notification" in window)) return;
            const permission = await Notification.requestPermission();
            notificationButton.textContent =
                permission === "granted"
                    ? "Notifications activées"
                    : "Notifications non autorisées";
            notificationButton.disabled = permission === "granted";
        });
    }

    messageList.scrollTop = messageList.scrollHeight;
    connect();
    window.addEventListener("beforeunload", function () {
        closing = true;
        clearTimeout(reconnectTimer);
        if (socket) socket.close();
    });
});
