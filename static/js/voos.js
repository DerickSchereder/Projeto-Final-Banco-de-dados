document.addEventListener("DOMContentLoaded", function() {
    
    const sliderPreco = document.getElementById('sliderPreco');
    const precoDisplay = document.getElementById('precoDisplay');
    const checkboxesParadas = document.querySelectorAll('.filtro-parada');
    const btnLimpar = document.getElementById('btnLimpar');
    const vooCards = document.querySelectorAll('.voo-card');

    // Atualiza o texto do slider de preço em tempo real
    sliderPreco.addEventListener('input', function() {
        const valorFormatado = Number(this.value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        precoDisplay.innerHTML = valorFormatado;
        filtrarVoos();
    });

    // Escuta cliques nos checkboxes de paradas
    checkboxesParadas.forEach(box => {
        box.addEventListener('change', filtrarVoos);
    });

    // Botão de limpar filtros
    btnLimpar.addEventListener('click', function() {
        sliderPreco.value = 5000;
        precoDisplay.innerHTML = 'R$ 5.000,00';
        checkboxesParadas.forEach(box => box.checked = false);
        filtrarVoos();
    });

    // A Lógica que esconde e mostra os cartões
    function filtrarVoos() {
        const precoMaximo = parseFloat(sliderPreco.value);
        
        // Pega quais caixas de parada estão marcadas
        const paradasMarcadas = Array.from(checkboxesParadas)
                                     .filter(box => box.checked)
                                     .map(box => box.value);

        vooCards.forEach(card => {
            const precoVoo = parseFloat(card.getAttribute('data-preco'));
            const paradasVoo = card.getAttribute('data-paradas');
            
            let mostrarPorPreco = precoVoo <= precoMaximo;
            let mostrarPorParada = paradasMarcadas.length === 0 || paradasMarcadas.includes(paradasVoo);

            // Se o voo de 2 paradas se enquadrar na opção "2 ou mais"
            if (paradasMarcadas.includes("2") && parseInt(paradasVoo) >= 2) {
                mostrarPorParada = true;
            }

            // Exibe ou esconde o cartão
            if (mostrarPorPreco && mostrarPorParada) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    }
});