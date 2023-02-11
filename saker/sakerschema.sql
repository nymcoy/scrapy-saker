DROP TABLE IF EXISTS articles;
CREATE TABLE articles (
	article_url VARCHAR(2000) PRIMARY KEY,
    article_path VARCHAR(2000) NOT NULL,
	article_id VARCHAR(10) NOT NULL,
	article_title VARCHAR(1000),
	article_date DATE,
	article_category VARCHAR(100),
	article_author VARCHAR(100)
);
DROP TABLE IF EXISTS links;
CREATE TABLE links (
	link_id INTEGER PRIMARY KEY AUTOINCREMENT,
	from_url VARCHAR(2000) NOT NULL,
	to_url VARCHAR(2000)
);
DROP TABLE IF EXISTS tags;
CREATE TABLE tags  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_url VARCHAR(2000) NOT NULL,
    tag VARCHAR(100) NOT NULL
);