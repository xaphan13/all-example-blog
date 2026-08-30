-- Esquema inicial: users, posts, tags, post_tags

CREATE TABLE users (
    id            serial PRIMARY KEY,
    username      text   UNIQUE NOT NULL,
    password_hash text   NOT NULL
);

CREATE TABLE posts (
    id            serial      PRIMARY KEY,
    slug          text        UNIQUE NOT NULL,
    title         text        NOT NULL,
    summary       text        NOT NULL DEFAULT '',
    cover_image   text,                          -- URL de la portada (tarjetas del inicio)
    content_md    text        NOT NULL DEFAULT '', -- fuente markdown (lo que se edita)
    content_html  text        NOT NULL DEFAULT '', -- HTML renderizado al guardar (lo que se sirve)
    published     boolean     NOT NULL DEFAULT false,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    published_at  timestamptz,

    -- Columna calculada por Postgres para búsqueda full-text:
    -- el título pesa más (A) que el resumen (B) y que el contenido (C).
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(content_md, '')), 'C')
    ) STORED
);

CREATE INDEX posts_search_idx ON posts USING GIN (search_vector);
CREATE INDEX posts_published_idx ON posts (published, published_at DESC);

CREATE TABLE tags (
    id   serial PRIMARY KEY,
    name text   NOT NULL,
    slug text   UNIQUE NOT NULL
);

CREATE TABLE post_tags (
    post_id int NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    tag_id  int NOT NULL REFERENCES tags (id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);
