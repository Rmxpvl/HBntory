export function setText (element, value = '') {
  if (element) {
    element.textContent = String(value);
  }
}

export function setVisible (element, visible) {
  if (element) {
    element.hidden = !visible;
  }
}

const STATE_ELEMENT_KEYS = {
  loading: 'loadingElement',
  error: 'errorElement',
  empty: 'emptyElement',
  results: 'resultsElement'
};

// Shows exactly one of loading / error / empty / results, hiding the rest.
export function showCatalogueState (state, elements) {
  for (const [key, elementKey] of Object.entries(STATE_ELEMENT_KEYS)) {
    setVisible(elements[elementKey], key === state);
  }
}

function formatPrice (product) {
  const price = Number(product.unit_price);

  if (!Number.isFinite(price)) {
    return null;
  }

  try {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: product.currency || 'EUR'
    }).format(price);
  } catch {
    return `${price} ${product.currency ?? ''}`.trim();
  }
}

export function createProductCard (product) {
  const card = document.createElement('li');
  card.className = 'product-card';

  if (product.category) {
    const category = document.createElement('span');
    category.className = 'product-card__category';
    category.textContent = product.category;
    card.appendChild(category);
  }

  const name = document.createElement('h3');
  name.className = 'product-card__name';
  name.textContent = product.name ?? 'Produit sans nom';
  card.appendChild(name);

  if (product.brand) {
    const brand = document.createElement('p');
    brand.className = 'product-card__brand';
    brand.textContent = product.brand;
    card.appendChild(brand);
  }

  if (product.description) {
    const description = document.createElement('p');
    description.className = 'product-card__description';
    description.textContent = product.description;
    card.appendChild(description);
  }

  if (product.discontinued) {
    const discontinued = document.createElement('span');
    discontinued.className = 'product-card__discontinued';
    discontinued.textContent = 'Discontinué';
    card.appendChild(discontinued);
  }

  const price = formatPrice(product);

  if (price) {
    const priceElement = document.createElement('p');
    priceElement.className = 'product-card__price';
    priceElement.textContent = price;
    card.appendChild(priceElement);
  }

  return card;
}

export function renderProductGrid (container, products) {
  if (!container) {
    return;
  }

  container.replaceChildren(...products.map(createProductCard));
}

export function populateCategoryOptions (selectElement, categories) {
  if (!selectElement) {
    return;
  }

  const currentValue = selectElement.value;

  const placeholder = selectElement.querySelector('option[value=""]');
  selectElement.replaceChildren(
    ...(placeholder ? [placeholder] : []),
    ...categories.map((category) => {
      const option = document.createElement('option');
      option.value = category.name;
      option.textContent = `${category.name} (${category.product_count})`;
      return option;
    })
  );

  selectElement.value = currentValue;
}
