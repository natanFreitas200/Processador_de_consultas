-- bd_vendas_schema.sql
CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;

-- Tabela: clientes
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(150),
    telefone VARCHAR(30),
    endereco TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_cliente),
    UNIQUE KEY ux_clientes_email (email)
) ENGINE=InnoDB;

-- Tabela: categorias
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(80) NOT NULL,
    descricao VARCHAR(255),
    PRIMARY KEY (id_categoria),
    UNIQUE KEY ux_categorias_nome (nome)
) ENGINE=InnoDB;

-- Tabela: produtos
CREATE TABLE IF NOT EXISTS produtos (
    id_produto INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    estoque INT NOT NULL DEFAULT 0,
    id_categoria INT UNSIGNED,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_produto),
    KEY idx_produtos_categoria (id_categoria),
    CONSTRAINT fk_produtos_categoria FOREIGN KEY (id_categoria)
        REFERENCES categorias (id_categoria) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Tabela: vendas
CREATE TABLE IF NOT EXISTS vendas (
    id_venda INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_cliente INT UNSIGNED,
    data_venda TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    status ENUM('pendente','pago','cancelada') NOT NULL DEFAULT 'pendente',
    PRIMARY KEY (id_venda),
    KEY idx_vendas_cliente (id_cliente),
    CONSTRAINT fk_vendas_clientes FOREIGN KEY (id_cliente)
        REFERENCES clientes (id_cliente) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Tabela: itens_venda
CREATE TABLE IF NOT EXISTS itens_venda (
    id_item INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_venda INT UNSIGNED NOT NULL,
    id_produto INT UNSIGNED NOT NULL,
    quantidade INT NOT NULL DEFAULT 1,
    preco_unit DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) AS (quantidade * preco_unit) STORED,
    PRIMARY KEY (id_item),
    KEY idx_itens_venda_venda (id_venda),
    KEY idx_itens_venda_produto (id_produto),
    CONSTRAINT fk_itens_venda_venda FOREIGN KEY (id_venda)
        REFERENCES vendas (id_venda) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_itens_venda_produto FOREIGN KEY (id_produto)
        REFERENCES produtos (id_produto) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Tabela: usuarios (opcional — para autenticação simples)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(60) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    nome_completo VARCHAR(120),
    papel ENUM('admin','vendedor') NOT NULL DEFAULT 'vendedor',
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY ux_usuarios_usuario (usuario)
) ENGINE=InnoDB;

-- Exemplo de dados: categorias
INSERT INTO categorias (nome, descricao) VALUES
('Eletrônicos', 'Aparelhos eletrônicos e acessórios'),
('Livros', 'Livros em geral'),
('Alimentos', 'Produtos alimentícios');

-- Exemplo de dados: produtos
INSERT INTO produtos (nome, descricao, preco, estoque, id_categoria) VALUES
('Fone de ouvido XYZ', 'Fone com cancelamento de ruído', 199.90, 50, 1),
('Livro: Aprendendo SQL', 'Guia prático de SQL', 59.90, 120, 2),
('Café em pó 500g', 'Café torrado e moído', 19.50, 200, 3);

-- Exemplo de dados: clientes
INSERT INTO clientes (nome, email, telefone, endereco) VALUES
('João Silva', 'joao.silva@example.com', '+55 11 99999-0001', 'Rua A, 123, São Paulo'),
('Maria Oliveira', 'maria.oliveira@example.com', '+55 21 98888-1111', 'Av. B, 456, Rio de Janeiro');

-- Exemplo de dados: vendas + itens_venda
INSERT INTO vendas (id_cliente, data_venda, total, status) VALUES
(1, NOW(), 259.80, 'pago'),
(2, NOW(), 19.50, 'pendente');

INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unit) VALUES
(1, 1, 1, 199.90),  -- fone
(1, 2, 1, 59.90),   -- livro
(2, 3, 1, 19.50);   -- café

-- Exemplo de dados: usuarios (senha_hash é só exemplo — use hashes reais em produção)
INSERT INTO usuarios (usuario, senha_hash, nome_completo, papel) VALUES
('admin', 'changeme-hash', 'Administrador', 'admin'),
('vendedor', 'changeme-hash', 'Vendedor Teste', 'vendedor');

-- Pequena verificação (opcional)
SELECT * FROM clientes;
SELECT * FROM produtos;
SELECT * FROM vendas;

