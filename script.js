document.addEventListener('DOMContentLoaded', () => {
    // ... (toda a parte inicial de obter elementos e lógica de tema continua a mesma)
    const chatOutput = document.getElementById('chat-output');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const API_URL = 'https://msv-stihl.github.io/chatbot_v1/dados.json';
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') { document.body.classList.add('dark-theme'); }
    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        if (document.body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
    function addMessage(message, sender, isHtml = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        if (isHtml) {
            messageDiv.innerHTML = message;
        } else {
            messageDiv.textContent = message;
        }
        chatOutput.appendChild(messageDiv);
        chatOutput.scrollTop = chatOutput.scrollHeight;
    }

    // --- FUNÇÃO fetchOSData ATUALIZADA ---
    async function fetchOSData(osNumber) {
        addMessage('Aguarde, estou buscando as informações...', 'bot');
        try {
            const response = await fetch(API_URL);
            const dataList = await response.json();
            const data = dataList.find(item => item.numero_os === osNumber)
            chatOutput.removeChild(chatOutput.lastChild); 

            if (response.ok) {
                // Mensagem 1: Detalhes da OS
                const respostaHtml = `
                    <strong>Detalhes da OS ${data.numero_os}:</strong><br>
                    - <strong>Status:</strong> ${data.status || 'Não informado'}<br>
                    - <strong>Prioridade:</strong> ${data.prioridade || 'Não informada'}<br>
                    - <strong>Data Prevista:</strong> ${data.data_prevista_formatada || 'Não definida'}<br>
                    - <strong>Descrição:</strong> ${data.descricao || 'Sem descrição'}
                `;
                addMessage(respostaHtml, 'bot', true);

                // Mensagem 2: Descrição do status
                if (data.descricao_status) {
                    setTimeout(() => {
                        addMessage(data.descricao_status, 'bot');
                    }, 700);
                }

                // Mensagem 3: Resumo dos chamados abertos
                if (data.contagem_abertos && Object.keys(data.contagem_abertos).length > 0) {
                    const mapaPrioTexto = { '1': 'ZU', '2': 'Alta', '3': 'Média', '4': 'Baixa', '5': 'Parada Programada', '6': 'Visita' };
                    let totalAbertos = 0;
                    let listaHtmlItens = '';
                    const prioridadesOrdenadas = Object.keys(data.contagem_abertos).sort();

                    const prioridadesValidas = ['1', '2', '3', '4', '5', '6'];
                    for (const prioCode of prioridadesOrdenadas) {
                        if (!prioCode || !prioridadesValidas.includes(prioCode.trim())) continue;
                        const contagem = data.contagem_abertos[prioCode];
                        totalAbertos += contagem;
                        const prioTexto = mapaPrioTexto[prioCode] || `Prioridade ${prioCode}`;
                        listaHtmlItens += `<li><strong>${contagem}</strong> em prioridade <strong>${prioTexto}</strong></li>`;
                    }
                    const resumoTexto = `Atualmente, temos um total de <strong>${totalAbertos}</strong> chamados em aberto 👇<ul>${listaHtmlItens}</ul>`;
                    
                    setTimeout(() => {
                        addMessage(resumoTexto, 'bot', true);
                    }, 1500); 
                }

                // --- INÍCIO DA NOVA LÓGICA DO LINK DE E-MAIL ---
                // Mensagem 4: Link para contato por e-mail
                setTimeout(() => {
                    // Monta o assunto do e-mail dinamicamente
                    const assuntoEmail = encodeURIComponent(`Dúvidas - OS ${data.numero_os}`);
                    
                    // Cria o link mailto completo
                    const linkEmail = `mailto:manserv@stihl.com.br?subject=${assuntoEmail}`;
                    
                    // Cria a mensagem final com o hyperlink
                    const mensagemEmail = `Caso queira tirar alguma dúvida específica dessa OS, <a href="${linkEmail}" target="_blank">clique aqui</a>.`;
                    
                    // Adiciona a mensagem ao chat
                    addMessage(mensagemEmail, 'bot', true);
                }, 2200); // Delay maior para ser a última mensagem a aparecer
                // --- FIM DA NOVA LÓGICA ---

            } else {
                addMessage(data.erro, 'bot');
            }
        } catch (error) {
            console.error('Erro de conexão:', error);
            chatOutput.removeChild(chatOutput.lastChild);
            addMessage('Desculpe, não consegui me conectar ao sistema. Verifique se o backend está rodando e tente novamente.', 'bot');
        }
    }

    // ... (o resto do arquivo script.js continua igual)
    function processMessage(message) {
        const lowerCaseMessage = message.toLowerCase();
        if (lowerCaseMessage.includes('olá') || lowerCaseMessage.includes('bom dia') || lowerCaseMessage.includes('boa tarde')) {
            addMessage('Olá! Como posso ajudar? Por favor, envie o número da OS que deseja consultar.', 'bot');
            return;
        }
        const osRegex = /\b(\d{9})\b/;
        const match = lowerCaseMessage.match(osRegex);
        if (match) {
            const osNumber = match[1];
            fetchOSData(osNumber);
        } else {
            addMessage('Não entendi. Por favor, envie uma mensagem contendo o número da OS.', 'bot');
        }
    }
    function handleUserInput() {
        const message = userInput.value.trim();
        if (!message) return;
        addMessage(message, 'user');
        userInput.value = '';
        processMessage(message);
    }
    sendBtn.addEventListener('click', handleUserInput);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleUserInput();
        }
    });
    addMessage('Olá! Me chamo S.A.M.A.N.T.H.A. - Sistema de Acompanhamento Manserv de Tratativas, Históricos e Atendimentos. Sou assistente virtual da Manserv, e irei ajudar com o seu atendimento. Por favor, informe o número do seu chamado através da ordem SAP. Exemplo: 820171234', 'bot');
});