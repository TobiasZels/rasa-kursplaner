const container = document.getElementById("chatarea");
const usermsgtemplate = document.getElementById("msgUser");
const botmsgtemplate = document.getElementById("msgBot");


eel.expose(botMessage);
function botMessage(input){
    let secondClone = botmsgtemplate.content.firstElementChild.cloneNode(true);
    secondClone.getElementsByClassName("chatbuble_bot")[0].textContent = input;
    container.appendChild(secondClone);
}

function sendMessage(input, event){
    let secondClone = usermsgtemplate.content.firstElementChild.cloneNode(true);
    secondClone.getElementsByClassName("chatbuble_user")[0].textContent = input;
    container.appendChild(secondClone);
    document.getElementById('msgInput').value = ""
    event.preventDefault();
}