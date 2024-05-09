document.addEventListener("DOMContentLoaded", function() {
  console.log("DOM content loaded");

  // Hide message-form initially
  document.getElementById("message-form").classList.add("hidden");

  let userCode = document.getElementById("user-code").textContent;

  var qrcode = new QRCode(document.getElementById("qrcode"), {
    text: userCode,
    width: 128,
    height: 128,
    colorDark : "#000000",
    colorLight : "#ffffff",
    correctLevel : QRCode.CorrectLevel.H
  });


  const html5Qrcode = new Html5Qrcode('reader');
  const config = { fps: 10, qrbox: { width: 250, height: 250 } };
  let isScanning = false;

  // Function to start QR code scanning
  const startQRScan = () => {
    if (!isScanning) {
      isScanning = true;
      html5Qrcode.start({ facingMode: "environment" }, config, qrCodeSuccessCallback);
    }
  };

  const qrCodeSuccessCallback = (decodedText, decodedResult) => {
    if (decodedText) {
      stopQRScan(); // Stop scanning
      document.getElementById("code-input").value = decodedText;
      document.getElementById("connect-btn").click();
      document.getElementById("overlay").style.display = "none"; // Close overlay
    }
  };

  const stopQRScan = () => {
    if (isScanning) {
      isScanning = false;
      html5Qrcode.stop();
    }
  };

  // Show QR reader overlay
  document.getElementById("scan-btn").addEventListener("click", function() {
    document.getElementById("overlay").style.display = "block";
    startQRScan();
  });

  // Close QR reader overlay
  document.getElementById("overlay").addEventListener("click", function(event) {
    if (event.target === this) {
      document.getElementById("overlay").style.display = "none";
      document.getElementById("reader-container").classList.remove("hidden");
      stopQRScan();
    }
  });

  // Add event listener to the button
  document.getElementById("scan-btn").addEventListener("click", startQRScan);

  var socket = new WebSocket("https://hordun.tech/portal/");

  socket.onopen = function(event) {
    console.log("WebSocket connection established");

    // Send data to backend
    socket.send(JSON.stringify({ event: "secret-code", code: userCode }));
  };

  // Add event listener to connect-form after DOM content is loaded
  document.getElementById("connect-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent the form from submitting normally

    codeInput = document.getElementById("code-input").value; // Set codeInput value

    socket.send(JSON.stringify({ event: "join", code: codeInput }));

  });

  // Add event listener for message-form submit
  document.getElementById("message-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent the form from submitting normally


    function generateRandomNumber(length) {
      var result = '';
      var characters = '0123456789abcdef';
      var charactersLength = characters.length;
      for (var i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
      }
      return result;
    }

    const sendMessage = () => {
      const messageInput = document.getElementById("message-input");
      const message = messageInput.value.trim();
      if (message === "") return;

      var secretKey = generateRandomNumber(32);
      var aesKey = CryptoJS.enc.Base64.parse(secretKey);
      var ivGen = Array.from({length: 16}, () => Math.floor(Math.random() * 10)).join('');
      var iv = CryptoJS.enc.Utf8.parse(ivGen);
      var encryptionOptions = {
        iv: iv,
        mode: CryptoJS.mode.CBC
      };
      var encryptedMessage = CryptoJS.AES.encrypt(message, aesKey, encryptionOptions).toString();
      var publicKey = forge.pki.publicKeyFromPem('-----BEGIN PUBLIC KEY-----\n'+
        'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/EqD04Y7XKJleTYDL9N7noeU2\n'+
        'q4fF0h9d1/8W25pZwFi+yhXWAsH/If8J02M5EuEdvI/y7dqa8f0EyQ3ceuRmIs7q\n'+
        '5SkDfueh3DgiEfJm2edYG5+k28klJCplZ7BwApkZgJZTBHPHt67yoHtcjFpbkpAF\n'+
        'fKCRwqLOCVT8+czrWwIDAQAB\n'+
        '-----END PUBLIC KEY-----');

      var encryptedKey = publicKey.encrypt(secretKey, "RSA-OAEP", {
        md: forge.md.sha256.create(),
        mgf1: forge.mgf1.create()
      });
      var base64 = forge.util.encode64(encryptedKey);
      code = document.getElementById("code-value").textContent
      socket.send(JSON.stringify({ event: "encryption", message: encryptedMessage, key: base64, iv: ivGen, code: code }));
    };

    sendMessage();
    document.getElementById("message-input").value = "";

  });
  // Handle user-join-response event from the server
  socket.onmessage = function(event) {
    try {
      var data = JSON.parse(event.data);
    }
    catch (error) {
      console.log('Error parsing JSON:', error, data);
    }
    if (data.kind === "Verify") {
      if (data.status === "CorrectCode") {
        let room_code = data.code;
        // Hide connect-form and show message-form
        document.getElementById("code-value").textContent = room_code;
        document.getElementById("connect-form").classList.add("hidden");
        document.getElementById("message-form").classList.remove("hidden");
      } else if (data.status === "SelfCode") {
        alert("Can't Use Your Own Code");
      } else if (data.status === "IncorrectCode") {
        alert("Wrong Code!!!");
      } else if (data.status === "Empty") {
        alert("You need to enter a code");
      }
    } else if (data.kind === "refresh") {
      if (data.status === "Reset") {
        alert("You are the only one left. Portal Closed.");
        location.reload();
      }
    } else if (data.kind === "messageSubmit") {
      if (data.sender === "isMe") {
        console.log("I am a sender")
        messageClass = "sender-message own";
        divClass = "inlineContainer own"
        timeClass = "own"
      } else {
        console.log("I am a receiver")
        messageClass = "receiver-message other";
        divClass = "inlineContainer other"
        timeClass = "other"
      }
      var timeUTC = new Date().toUTCString().slice(-12, -7);
      // Unhide the message box
      document.getElementById("message-box").classList.remove("hidden");
      document.getElementById("message-box").classList.add("scrollable");

      // Append the received message to the message box with appropriate styling
      var messageElement = `
                    <div class="bubbleWrapper">
                        <div class="${divClass}">
                            <img class="inlineIcon" src="https://cdn1.iconfinder.com/data/icons/ninja-things-1/1772/ninja-simple-512.png">
                            <p class="${messageClass}">${data.message}</p>
                        </div>
                    <span class="${timeClass}">${timeUTC}</span>
                    </div>
                `;

      var messageBox = document.getElementById("message-box");
      messageBox.innerHTML += messageElement;

      // Scroll to the bottom of the message box
      messageBox.scrollTop = messageBox.scrollHeight;
    }
  };

  socket.onclose = function(event) {
    console.log("Websocket Closed Gracefully")
    socket.send(JSON.stringify({ event: "refresh"}));
  };
});
