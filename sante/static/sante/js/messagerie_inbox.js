document.addEventListener("DOMContentLoaded", function () {
    const list = document.getElementById("conversationList");
    if (!list) return;

    const notificationButton = document.getElementById("enableInboxNotifications");
    let socket;
    let retryCount = 0;
    let reconnectTimer;
    let closing = false;

    function showNotification(data) {
        if (
            document.visibilityState === "visible" ||
            !("Notification" in window) ||
            Notification.permission !== "granted"
        ) return;

        new Notification("Nouveau message de " + data.sender_name, {
            body: data.text,
            tag: "toukpedio-conversation-" + data.conversation_id
        });
    }

    function updateConversation(data) {
        let link = list.querySelector(
            '[data-conversation-id="' + data.conversation_id + '"]'
        );
        const emptyInbox = document.getElementById("emptyInbox");

        if (!link) {
            if (emptyInbox) emptyInbox.remove();
            link = document.createElement("a");
            link.className = "list-group-item list-group-item-action p-3";
            link.dataset.conversationId = String(data.conversation_id);
            link.href = "/messagerie/" + data.conversation_id + "/";

            const layout = document.createElement("div");
            layout.className = "d-flex justify-content-between gap-3";
            const details = document.createElement("div");
            details.className = "min-w-0";
            const participant = document.createElement("div");
            participant.className = "fw-semibold";
            participant.textContent = data.sender_name;
            if (data.child_name) {
                participant.append(
                    document.createTextNode(" · " + data.child_name)
                );
            }
            const subject = document.createElement("div");
            subject.className = "conversation-subject";
            subject.textContent = data.subject;
            const preview = document.createElement("small");
            preview.className = "text-muted live-preview";
            details.append(participant, subject, preview);

            const metadata = document.createElement("div");
            metadata.className = "text-end";
            const badge = document.createElement("span");
            badge.className = "badge rounded-pill bg-success unread-badge";
            metadata.appendChild(badge);
            layout.append(details, metadata);
            link.appendChild(layout);
            list.prepend(link);
        }

        const preview = link.querySelector(".live-preview") ||
            link.querySelector("small.text-muted");
        if (preview) {
            const sentAt = new Date(data.sent_at);
            preview.textContent = "Dernier message " + (
                Number.isNaN(sentAt.getTime())
                    ? ""
                    : sentAt.toLocaleString("fr-FR", {
                        dateStyle: "short",
                        timeStyle: "short"
                    })
            );
        }

        let badge = link.querySelector(".unread-badge");
        if (!badge) {
            const metadata = link.querySelector(".text-end");
            badge = document.createElement("span");
            badge.className = "badge rounded-pill bg-success unread-badge";
            metadata.prepend(badge);
        }
        badge.textContent = data.unread_count + " non lu" +
            (data.unread_count > 1 ? "s" : "");
        badge.hidden = data.unread_count < 1;
        list.prepend(link);
    }

    function connect() {
        socket = new WebSocket(list.dataset.inboxWebsocketUrl);
        socket.addEventListener("open", function () {
            retryCount = 0;
        });
        socket.addEventListener("message", function (event) {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (error) {
                return;
            }
            if (data.type === "conversation_update") {
                updateConversation(data);
                showNotification(data);
            } else if (data.type === "unread_count") {
                const link = list.querySelector(
                    '[data-conversation-id="' + data.conversation_id + '"]'
                );
                const badge = link && link.querySelector(".unread-badge");
                if (badge) {
                    badge.textContent = data.unread_count + " non lu" +
                        (data.unread_count > 1 ? "s" : "");
                    badge.hidden = data.unread_count < 1;
                }
            }
        });
        socket.addEventListener("close", function () {
            if (!closing && retryCount < 8) {
                const delay = Math.min(1000 * (2 ** retryCount), 15000);
                retryCount += 1;
                reconnectTimer = setTimeout(connect, delay);
            }
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

    connect();
    window.addEventListener("beforeunload", function () {
        closing = true;
        clearTimeout(reconnectTimer);
        if (socket) socket.close();
    });
});
