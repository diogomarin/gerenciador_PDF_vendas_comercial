let cart = [];

document.getElementById('uploadForm')?.addEventListener('submit', function(e) {
    e.preventDefault();

    // Exibe a mensagem de extração em andamento
    document.getElementById('loadingMessage').style.display = 'block';

    let formData = new FormData(this);
    
    fetch('/upload_pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(html => {
        // Substitui o conteúdo da página com o HTML retornado
        document.body.innerHTML = html;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function addToCart() {
    const selectedItems = document.querySelectorAll('input[name="selected_items"]:checked');
    
    if (selectedItems.length === 0) {
        alert("Por favor, selecione pelo menos um item para adicionar ao carrinho.");
        return;
    }

    const cartItemsBody = document.getElementById('cartItemsBody');
    let cartItemsInput = document.getElementById('cartItemsInput');
    
    selectedItems.forEach(item => {
        const itemId = item.value;
        const row = item.closest('tr');
        const descricao = row.querySelector('td:nth-child(4)').innerText;
        const preco = row.querySelector('td:nth-child(6)').innerText;

        const existingItem = cart.find(i => i.descricao === descricao && i.preco === preco);
        if (existingItem) {
            existingItem.quantidade = parseInt(existingItem.quantidade) + 1;
        } else {
            cart.push({ descricao, preco });
            const newRow = document.createElement('tr');
            newRow.innerHTML = `<td>${descricao}</td><td>${preco}</td>`;
            cartItemsBody.appendChild(newRow);
        }
    });

    cartItemsInput.value = JSON.stringify(cart);
}
