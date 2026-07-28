INSERT INTO events (id, title, description, event_date, location, image_url, status) VALUES
(1, '演唱會一', '體驗未來音樂的視聽饗宴', '2025-12-15 19:00:00+08', '台北 Cyber Arena', 'https://images.unsplash.com/photo-1459749411177-718bf998e889?w=1200', 'published'),
(2, '演唱會二', '與科技界領袖一同探索創新與未來，為期一天的知識盛宴', '2025-11-30 09:00:00+08', '台北國際會議中心', 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1200', 'published'),
(3, '聖誕交響樂之夜', '與國家交響樂團共度浪漫的聖誕夜', '2025-12-24 20:00:00+08', '國家音樂廳', 'https://pyxis.nymag.com/v1/imgs/625/392/19e6ad61bd706ff522b43b9b30530f613c-17-paul-mccarthy-tree.2x.h473.w710.jpg', 'published')
ON CONFLICT (id) DO NOTHING;

INSERT INTO tickets (id, event_id, ticket_type, price, total_quantity, available_quantity) VALUES
(1, 1, '一般票', 2500.00, 1000, 1000),
(2, 2, '一般票', 1200.00, 500, 500),
(3, 3, '一般票', 3000.00, 800, 800)
ON CONFLICT (id) DO NOTHING;

SELECT setval('events_id_seq', (SELECT MAX(id) FROM events));
SELECT setval('tickets_id_seq', (SELECT MAX(id) FROM tickets));
EOF