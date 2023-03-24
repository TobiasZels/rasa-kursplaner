const container = document.getElementById("chatarea");
const usermsgtemplate = document.getElementById("msgUser");
const botmsgtemplate = document.getElementById("msgBot");
let chatActive = false

eel.expose(botMessage);
function botMessage(input){
    let secondClone = botmsgtemplate.content.firstElementChild.cloneNode(true);
    secondClone.getElementsByClassName("chatbuble_bot")[0].textContent = input;
    container.appendChild(secondClone);
    const el = document.getElementById('chatarea');
    // id of the chat container ---------- ^^^
    if (el) {
        el.scrollTop = el.scrollHeight;
    }
        
}

eel.expose(activateChat);
function activateChat(){
    document.getElementById("msgInput").disabled = false;
}

function sendMessage(input, event){
    let secondClone = usermsgtemplate.content.firstElementChild.cloneNode(true);
    secondClone.getElementsByClassName("chatbuble_user")[0].textContent = input;
    container.appendChild(secondClone);
    document.getElementById('msgInput').value = ""
    event.preventDefault();
    eel.returnChat(input)
    document.getElementById("msgInput").disabled = true;
    const el = document.getElementById('chatarea');
    // id of the chat container ---------- ^^^
    if (el) {
        el.scrollTop = el.scrollHeight;
    }
}