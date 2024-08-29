let cart = JSON.parse(localStorage.getItem('cart')) || [];

document.addEventListener('DOMContentLoaded', function () {
    loadCartItems();  // Carrega os itens do carrinho ao carregar a página

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
            document.body.innerHTML = html;
        })
        .catch(error => {
            console.error('Error:', error);
        });
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
        if (!existingItem) {
            cart.push({ descricao, preco });
            const newRow = document.createElement('tr');
            newRow.innerHTML = `<td>${descricao}</td><td>${preco}</td>`;
            cartItemsBody.appendChild(newRow);
        }
    });

    cartItemsInput.value = JSON.stringify(cart);
    localStorage.setItem('cart', JSON.stringify(cart));  // Salva o estado do carrinho no localStorage
}

function loadCartItems() {
    const cartItemsBody = document.getElementById('cartItemsBody');
    const cartItemsInput = document.getElementById('cartItemsInput');
    
    if (cart.length > 0) {
        cart.forEach(item => {
            const newRow = document.createElement('tr');
            newRow.innerHTML = `<td>${item.descricao}</td><td>${item.preco}</td>`;
            cartItemsBody.appendChild(newRow);
        });
        cartItemsInput.value = JSON.stringify(cart);
    }
}


document.getElementById('saveCartForm')?.addEventListener('submit', function() {
    // Limpa o localStorage após o carrinho ser salvo
    localStorage.removeItem('cart');
});
