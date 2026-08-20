// src/data/marketplaceData.js
// This will be shared between seller and marketplace

export const marketplaceProducts = [
  {
    id: 1,
    name: "Handwoven Bamboo Basket Set",
    price: 850,
    rating: 4.8,
    reviews: 42,
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=400&h=400&fit=crop&crop=center",
    location: "Manipur",
    category: "Baskets & Storage",
    seller: "Meera Textiles",
    stock: 15,
    unit: "set of 3",
    createdAt: "2026-01-15",
  },
  {
    id: 2,
    name: "Madhubani Painting — Radha Krishna",
    price: 2500,
    rating: 4.9,
    reviews: 56,
    image: "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=400&h=400&fit=crop&crop=center",
    location: "Bihar",
    category: "Art & Paintings",
    seller: "Madhubani Art House",
    stock: 3,
    unit: "painting",
    createdAt: "2026-01-14",
  },
  {
    id: 3,
    name: "Terracotta Pottery Set",
    price: 1200,
    rating: 4.7,
    reviews: 38,
    image: "https://images.unsplash.com/photo-1578749556568-bc2c0-1b2c3e0e9b6f?w=400&h=400&fit=crop&crop=center",
    location: "Rajasthan",
    category: "Pottery & Ceramics",
    seller: "Jaipur Pottery Works",
    stock: 0,
    unit: "set of 4",
    createdAt: "2026-01-13",
  },
  {
    id: 4,
    name: "Handwoven Silk Shawl",
    price: 2400,
    rating: 4.9,
    reviews: 128,
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=400&h=400&fit=crop&crop=center",
    location: "Varanasi",
    category: "Textiles & Fabric",
    seller: "Varanasi Silk House",
    stock: 12,
    unit: "shawl",
    createdAt: "2026-01-12",
  },
  {
    id: 5,
    name: "Wooden Carved Elephant",
    price: 1800,
    rating: 4.6,
    reviews: 29,
    image: "https://images.unsplash.com/photo-1564460576150-5a9d8d8e5e7f?w=400&h=400&fit=crop&crop=center",
    location: "Rajasthan",
    category: "Wood Craft",
    seller: "Rajasthan Woodworks",
    stock: 8,
    unit: "piece",
    createdAt: "2026-01-11",
  },
  {
    id: 6,
    name: "Brass Decorative Lamp",
    price: 3100,
    rating: 4.7,
    reviews: 67,
    image: "https://images.unsplash.com/photo-1578749556568-bc2c0-1b2c3e0e9b6f?w=400&h=400&fit=crop&crop=center",
    location: "Moradabad",
    category: "Metal Craft",
    seller: "Brass Crafts India",
    stock: 0,
    unit: "lamp",
    createdAt: "2026-01-10",
  },
  {
    id: 7,
    name: "Kantha Embroidery Quilt",
    price: 4500,
    rating: 4.9,
    reviews: 342,
    image: "https://images.unsplash.com/photo-1583496661160-fb5886a0f5c8?w=400&h=400&fit=crop&crop=center",
    location: "West Bengal",
    category: "Textiles & Fabric",
    seller: "Kantha Creations",
    stock: 5,
    unit: "quilt",
    createdAt: "2026-01-09",
  },
  {
    id: 8,
    name: "Blue Pottery Dinner Set",
    price: 2800,
    rating: 4.6,
    reviews: 89,
    image: "https://images.unsplash.com/photo-1578749556568-bc2c0-1b2c3e0e9b6f?w=400&h=400&fit=crop&crop=center",
    location: "Jaipur",
    category: "Pottery & Ceramics",
    seller: "Blue Pottery House",
    stock: 10,
    unit: "set of 6",
    createdAt: "2026-01-08",
  },
  {
    id: 9,
    name: "Warli Art Painting",
    price: 1500,
    rating: 4.8,
    reviews: 45,
    image: "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=400&h=400&fit=crop&crop=center",
    location: "Maharashtra",
    category: "Art & Paintings",
    seller: "Warli Art Studio",
    stock: 7,
    unit: "painting",
    createdAt: "2026-01-07",
  },
  {
    id: 10,
    name: "Handwoven Cotton Bags",
    price: 650,
    rating: 4.5,
    reviews: 73,
    image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=400&h=400&fit=crop&crop=center",
    location: "Chhattisgarh",
    category: "Textiles & Fabric",
    seller: "Chhattisgarh Weavers",
    stock: 20,
    unit: "bag",
    createdAt: "2026-01-06",
  },
];

// Function to add product from seller
export const addMarketplaceProduct = (product) => {
  const newProduct = {
    ...product,
    id: marketplaceProducts.length + 1,
    createdAt: new Date().toISOString().split('T')[0],
  };
  marketplaceProducts.push(newProduct);
  return newProduct;
};

// Function to update stock from seller
export const updateProductStock = (productId, newStock) => {
  const product = marketplaceProducts.find(p => p.id === productId);
  if (product) {
    product.stock = newStock;
    return product;
  }
  return null;
};

// Function to get all active products (in stock)
export const getActiveProducts = () => {
  return marketplaceProducts.filter(p => p.stock > 0);
};

// Function to get product by ID
export const getProductById = (id) => {
  return marketplaceProducts.find(p => p.id === id);
};