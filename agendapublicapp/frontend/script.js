// ============================================================
// AGENDAPUBLICAPP - FRONTEND (JavaScript)
// ============================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { 
    getAuth, 
    signInWithEmailAndPassword, 
    signInWithPopup, 
    GoogleAuthProvider, 
    onAuthStateChanged, 
    signOut 
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js";

// Configuração do Firebase
const firebaseConfig = {
    apiKey: "AIzaSyCv-vT1AXb-olZYPOQfOypIEGT8qznEQog",
    authDomain: "agendapublicapp.firebaseapp.com",
    projectId: "agendapublicapp",
    storageBucket: "agendapublicapp.firebasestorage.app",
    messagingSenderId: "325880421307",
    appId: "1:325880421307:web:f64847bfc7b653be92c29e",
    measurementId: "G-CGHLDGHW3B"
};

// Inicialização
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

const API_URL = window.location.origin + '/api';

// ============================================================
// CONFIGURAÇÃO INICIAL E AUTENTICAÇÃO
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    // Referências de UI
    const loginSection = document.getElementById('login-section');
    const mainApp = document.getElementById('main-app');
    const btnLogout = document.getElementById('btn-logout');
    const loginForm = document.getElementById('login-form');
    const btnGoogleLogin = document.getElementById('btn-google-login');

    // Monitorar estado de autenticação
    onAuthStateChanged(auth, (user) => {
        if (user) {
            // Usuário logado
            loginSection.style.display = 'none';
            mainApp.style.display = 'block';
            btnLogout.style.display = 'block';
            console.log("Usuário logado:", user.email);
            
            // Carregar os dados do dashboard apenas quando logado
            carregarDados();
        } else {
            // Usuário não logado
            loginSection.style.display = 'flex';
            mainApp.style.display = 'none';
            btnLogout.style.display = 'none';
        }
    });

    // Login com E-mail/Senha
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        signInWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                console.log("Login com email bem sucedido!");
            })
            .catch((error) => {
                alert("Erro ao fazer login: " + error.message);
            });
    });

    // Login com Google
    btnGoogleLogin.addEventListener('click', () => {
        signInWithPopup(auth, googleProvider)
            .then((result) => {
                console.log("Login com Google bem sucedido!");
            })
            .catch((error) => {
                alert("Erro ao fazer login com Google: " + error.message);
            });
    });

    // Botão Sair (Logout)
    btnLogout.addEventListener('click', () => {
        signOut(auth).then(() => {
            console.log("Deslogado com sucesso");
        }).catch((error) => {
            console.error("Erro ao deslogar", error);
        });
    });
});

// ============================================================
// FUNÇÕES PRINCIPAIS
// ============================================================

async function carregarDados() {
    try {
        // 1. Status do sistema
        const statusResponse = await fetch(API_URL.replace('/api', '/'));
        const statusData = await statusResponse.json();
        document.getElementById('status-text').textContent = `Online - ${statusData.nome} v${statusData.versao}`;

        // 2. Análise completa
        const analiseResponse = await fetch(`${API_URL}/analise`);
        const analiseData = await analiseResponse.json();

        if (analiseData.erro) {
            document.getElementById('status-text').textContent = '❌ ' + analiseData.erro;
            return;
        }

        // 3. Atualizar cards
        document.getElementById('total-eventos').textContent = analiseData.total_eventos || 0;
        
        const score = analiseData.score_paralisacao || 0;
        document.getElementById('score-efetividade').textContent = (score * 100).toFixed(0) + '%';

        // 4. Recomendação
        const recomendacaoDiv = document.getElementById('recomendacao-content');
        if (analiseData.recomendacao) {
            const nivel = analiseData.recomendacao.nivel;
            const emoji = nivel === 'alta' ? '✅' : '⚠️';
            const classe = nivel === 'alta' ? 'alta' : 'media';
            
            recomendacaoDiv.innerHTML = `
                <div class="recomendacao ${classe}">
                    <p class="recomendacao-emoji">${emoji}</p>
                    <p class="recomendacao-titulo">${analiseData.recomendacao.mensagem}</p>
                    <p class="recomendacao-acao">🎯 ${analiseData.recomendacao.acao}</p>
                </div>
            `;
        }

        // 5. Gráficos
        carregarGrafico('grafico-atores', 'impacto_atores');
        carregarGrafico('grafico-evolucao', 'evolucao');
        carregarGrafico('grafico-correlacao', 'correlacao');

    } catch (error) {
        document.getElementById('status-text').textContent = '❌ Erro ao conectar: ' + error.message;
        console.error(error);
    }
}

async function carregarGrafico(elementId, tipo) {
    try {
        const response = await fetch(`${API_URL}/grafico/${tipo}`);
        const data = await response.json();
        
        if (data.imagem) {
            document.getElementById(elementId).src = 'data:image/png;base64,' + data.imagem;
        } else if (data.erro) {
            console.error('Erro na API ao carregar gráfico ' + tipo + ':', data.erro);
        }
    } catch (error) {
        console.error('Erro ao carregar gráfico ' + tipo, error);
    }
}
