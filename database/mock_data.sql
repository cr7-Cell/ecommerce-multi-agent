-- ============================================================
-- 跨境电商多智能体系统 - 模拟数据集
-- 为所有 14 张核心表生成合理的模拟数据
-- ============================================================

-- ============================================================
-- 1. 供应商数据
-- ============================================================
INSERT INTO suppliers (name, contact_person, email, phone, country, address, rating, lead_time_days) VALUES
('深圳华强电子有限公司', '张伟', 'zhangwei@huaqiang.cn', '+86-755-12345678', '中国', '深圳市福田区华强北路1001号', 4.5, 7),
('广州服装贸易集团', '李芳', 'lifang@gzgarment.cn', '+86-20-87654321', '中国', '广州市天河区体育西路200号', 4.2, 10),
('GlobalTech Inc.', 'John Smith', 'john@globaltech.com', '+1-415-555-0101', '美国', '123 Tech Park, Silicon Valley, CA', 4.8, 14),
('义乌小商品批发城', '王磊', 'wanglei@yiwu.cn', '+86-579-12345678', '中国', '义乌市国际商贸城3区', 4.0, 5),
('Korean Beauty Supply', 'Kim Min-ji', 'minji@kbeauty.kr', '+82-2-1234-5678', '韩国', 'Seoul, Gangnam-gu, 123 Beauty Street', 4.6, 8),
('Tokyo Electronics Co.', 'Tanaka Hiroshi', 'tanaka@tokyo-elec.jp', '+81-3-1234-5678', '日本', 'Tokyo, Chiyoda-ku, 1-2-3 Marunouchi', 4.7, 5);

-- ============================================================
-- 2. 仓库数据
-- ============================================================
INSERT INTO warehouses (name, code, country, city, address, capacity) VALUES
('深圳主仓', 'WH-SZ01', '中国', '深圳', '深圳市宝安区福永街道物流园A1', 50000),
('美国洛杉矶仓', 'WH-LA01', '美国', '洛杉矶', '1234 Logistics Dr, Los Angeles, CA 90001', 30000),
('德国法兰克福仓', 'WH-FR01', '德国', '法兰克福', 'Lagerstraße 100, 60327 Frankfurt', 20000),
('日本东京仓', 'WH-TK01', '日本', '东京', '東京都江東区物流センター1-2-3', 15000),
('英国伦敦仓', 'WH-LD01', '英国', '伦敦', '45 Warehouse Rd, London E1 6AN', 18000);

-- ============================================================
-- 3. 用户数据（10条）
-- ============================================================
INSERT INTO users (username, email, password_hash, phone, full_name, gender, birth_date, country, city, language, preferences, membership_level, reward_points) VALUES
('alice_wang', 'alice.wang@email.com', '$2b$12$hash_alice_wang', '+1-415-111-0001', 'Alice Wang', 'female', '1992-03-15', '美国', '旧金山', 'en', '{"categories":["electronics","fashion","beauty"],"price_range":{"min":10,"max":500},"brands":["Apple","Nike","Samsung"],"shopping_frequency":"weekly"}', 'gold', 2500),
('bob_zhang', 'bob.zhang@email.com', '$2b$12$hash_bob_zhang', '+1-212-222-0002', 'Bob Zhang', 'male', '1988-07-22', '美国', '纽约', 'en', '{"categories":["electronics","sports","books"],"price_range":{"min":20,"max":1000},"brands":["Sony","Adidas"],"shopping_frequency":"monthly"}', 'silver', 1200),
('cathy_li', 'cathy.li@email.com', '$2b$12$hash_cathy_li', '+44-20-333-0003', 'Cathy Li', 'female', '1995-11-08', '英国', '伦敦', 'en', '{"categories":["fashion","beauty","home"],"price_range":{"min":5,"max":300},"brands":["Zara","HM","Loreal"],"shopping_frequency":"weekly"}', 'gold', 3200),
('david_chen', 'david.chen@email.com', '$2b$12$hash_david_chen', '+86-138-444-0004', 'David Chen', 'male', '1990-01-30', '中国', '上海', 'zh', '{"categories":["electronics","gaming","sports"],"price_range":{"min":50,"max":2000},"brands":["Apple","Sony","Nintendo"],"shopping_frequency":"monthly"}', 'platinum', 5800),
('emma_liu', 'emma.liu@email.com', '$2b$12$hash_emma_liu', '+1-310-555-0005', 'Emma Liu', 'female', '1993-06-18', '美国', '洛杉矶', 'en', '{"categories":["beauty","fashion","health"],"price_range":{"min":10,"max":200},"brands":["Sephora","Lululemon"],"shopping_frequency":"weekly"}', 'silver', 800),
('frank_wu', 'frank.wu@email.com', '$2b$12$hash_frank_wu', '+49-30-666-0006', 'Frank Wu', 'male', '1985-09-12', '德国', '柏林', 'de', '{"categories":["electronics","automotive","tools"],"price_range":{"min":30,"max":1500},"brands":["Bosch","Siemens"],"shopping_frequency":"monthly"}', 'gold', 2100),
('grace_yang', 'grace.yang@email.com', '$2b$12$hash_grace_yang', '+81-3-777-0007', 'Grace Yang', 'female', '1997-04-25', '日本', '东京', 'ja', '{"categories":["beauty","fashion","food"],"price_range":{"min":5,"max":250},"brands":["Shiseido","Uniqlo"],"shopping_frequency":"weekly"}', 'silver', 950),
('henry_zhou', 'henry.zhou@email.com', '$2b$12$hash_henry_zhou', '+1-650-888-0008', 'Henry Zhou', 'male', '1991-12-03', '美国', '圣何塞', 'en', '{"categories":["electronics","software","books"],"price_range":{"min":20,"max":800},"brands":["Apple","Microsoft","Google"],"shopping_frequency":"monthly"}', 'gold', 1800),
('ivy_sun', 'ivy.sun@email.com', '$2b$12$hash_ivy_sun', '+86-139-999-0009', 'Ivy Sun', 'female', '1994-08-20', '中国', '成都', 'zh', '{"categories":["fashion","beauty","food","home"],"price_range":{"min":10,"max":400},"brands":["SK-II","Estee Lauder"],"shopping_frequency":"weekly"}', 'platinum', 4500),
('jack_ma', 'jack.ma@email.com', '$2b$12$hash_jack_ma', '+1-408-101-0010', 'Jack Ma', 'male', '1986-02-14', '美国', '西雅图', 'en', '{"categories":["electronics","sports","outdoor"],"price_range":{"min":50,"max":3000},"brands":["Apple","Canon","Patagonia"],"shopping_frequency":"monthly"}', 'gold', 2800);

-- ============================================================
-- 4. 商品数据（20条）
-- ============================================================
INSERT INTO products (sku, name, name_en, description, description_en, category_id, brand, base_price, sale_price, currency, cost_price, stock_quantity, min_stock, attributes, main_image_url, target_market, hs_code, status, supplier_id) VALUES
('SKU-BT-001', '蓝牙降噪耳机 Pro', 'Bluetooth Noise Cancelling Headphones Pro', '高品质主动降噪蓝牙耳机，40小时续航，支持Hi-Res音频', 'Premium active noise cancelling Bluetooth headphones with 40hr battery life and Hi-Res audio support', 1, 'AudioMax', 199.99, 159.99, 'USD', 85.00, 500, 50, '{"color":["black","white","blue"],"weight_kg":0.25,"connectivity":"Bluetooth 5.3"}', 'https://images.example.com/bt-headphone-pro.jpg', 'US', '85183000', 'active', 1),
('SKU-BT-002', '无线充电器 15W', '15W Wireless Charger', '支持iPhone和Android的快速无线充电器', 'Fast wireless charger compatible with iPhone and Android', 1, 'PowerUp', 29.99, 24.99, 'USD', 8.50, 1200, 100, '{"color":["black","white"],"weight_kg":0.08,"power_w":15}', 'https://images.example.com/wireless-charger.jpg', 'GLOBAL', '85044000', 'active', 1),
('SKU-FS-001', '女士夏季连衣裙', 'Women Summer Dress', '轻盈透气的纯棉连衣裙，多种花色可选', 'Lightweight breathable cotton dress with multiple patterns', 2, 'StyleMe', 69.99, 49.99, 'USD', 18.00, 300, 30, '{"color":["red","blue","floral"],"size":["S","M","L","XL"],"material":"100% cotton"}', 'https://images.example.com/summer-dress.jpg', 'US', '62044200', 'active', 2),
('SKU-FS-002', '男士运动跑鞋', 'Men Running Shoes', '轻量透气跑鞋，缓震科技，适合日常跑步', 'Lightweight breathable running shoes with cushioning technology', 2, 'RunFast', 129.99, 99.99, 'USD', 42.00, 450, 50, '{"color":["black","grey","navy"],"size":["7","8","9","10","11","12"],"weight_kg":0.28}', 'https://images.example.com/running-shoes.jpg', 'US', '64041100', 'active', 2),
('SKU-BT-003', '智能手表 Ultra', 'Smart Watch Ultra', '1.5寸AMOLED屏，心率血氧监测，GPS，50米防水', '1.5" AMOLED display, heart rate & SpO2, GPS, 50m water resistant', 1, 'TechWear', 349.99, 299.99, 'USD', 150.00, 200, 20, '{"color":["black","silver","gold"],"weight_kg":0.06,"screen_size_inch":1.5}', 'https://images.example.com/smart-watch.jpg', 'GLOBAL', '85176200', 'active', 3),
('SKU-BT-004', 'USB-C 集线器 7合1', 'USB-C Hub 7-in-1', 'Type-C多功能扩展坞，支持HDMI、USB3.0、SD卡', 'Type-C multiport hub with HDMI, USB3.0, SD card reader', 1, 'ConnectPro', 49.99, 39.99, 'USD', 15.00, 800, 80, '{"color":["space grey","silver"],"weight_kg":0.12,"ports":7}', 'https://images.example.com/usb-hub.jpg', 'GLOBAL', '84718000', 'active', 1),
('SKU-BT-005', '便携蓝牙音箱', 'Portable Bluetooth Speaker', 'IPX7防水，20W立体声，12小时播放', 'IPX7 waterproof, 20W stereo sound, 12hr playtime', 1, 'AudioMax', 79.99, 59.99, 'USD', 28.00, 600, 60, '{"color":["black","red","blue","green"],"weight_kg":0.55,"power_w":20}', 'https://images.example.com/bt-speaker.jpg', 'GLOBAL', '85182200', 'active', 1),
('SKU-BT-002', '4K网络摄像头', '4K Webcam Pro', '超高清4K摄像头，自动对焦，内置降噪麦克风', 'Ultra HD 4K webcam with autofocus and built-in noise-cancelling mic', 1, 'ClearView', 129.99, 99.99, 'USD', 55.00, 350, 35, '{"color":["black"],"weight_kg":0.15,"resolution":"4K"}', 'https://images.example.com/webcam.jpg', 'GLOBAL', '85258000', 'active', 3),
('SKU-FS-003', '防晒霜 SPF50+', 'Sunscreen SPF50+', '清爽不油腻的高倍防晒霜，适合所有肤质', 'Lightweight non-greasy high protection sunscreen for all skin types', 3, 'SkinGuard', 24.99, 19.99, 'USD', 7.00, 2000, 200, '{"size_ml":50,"spf":50,"water_resistant":true}', 'https://images.example.com/sunscreen.jpg', 'GLOBAL', '33049900', 'active', 5),
('SKU-FS-004', '精华液 - 玻尿酸保湿', 'Hyaluronic Acid Serum', '高浓度玻尿酸精华，深层补水保湿', 'High concentration hyaluronic acid serum for deep hydration', 3, 'SkinGuard', 39.99, 29.99, 'USD', 10.00, 1500, 150, '{"size_ml":30,"skin_type":"all","key_ingredient":"hyaluronic_acid"}', 'https://images.example.com/serum.jpg', 'GLOBAL', '33049900', 'active', 5),
('SKU-HM-001', '智能LED台灯', 'Smart LED Desk Lamp', '可调色温和亮度，支持手机APP控制', 'Adjustable color temperature and brightness with app control', 4, 'HomeSmart', 59.99, 49.99, 'USD', 22.00, 400, 40, '{"color":["white","black"],"weight_kg":0.8,"power_w":12}', 'https://images.example.com/desk-lamp.jpg', 'GLOBAL', '94052000', 'active', 1),
('SKU-FS-005', '瑜伽垫 6mm', 'Yoga Mat 6mm', '防滑TPE材质，双面纹理，附带绑带', 'Non-slip TPE material, double-sided texture with carrying strap', 5, 'FitLife', 39.99, 34.99, 'USD', 12.00, 700, 70, '{"color":["purple","blue","pink","grey"],"thickness_mm":6,"material":"TPE"}', 'https://images.example.com/yoga-mat.jpg', 'GLOBAL', '95069100', 'active', 2),
('SKU-TY-001', '儿童积木套装 200粒', 'Building Blocks Set 200pcs', '安全环保ABS材质，兼容主流品牌', 'Safe eco-friendly ABS material, compatible with major brands', 6, 'BuildFun', 49.99, 39.99, 'USD', 15.00, 600, 60, '{"pieces":200,"age_range":"3-12","material":"ABS"}', 'https://images.example.com/building-blocks.jpg', 'GLOBAL', '95030000', 'active', 4),
('SKU-FD-001', '有机绿茶 100g', 'Organic Green Tea 100g', '高山有机绿茶，清新回甘', 'High mountain organic green tea, fresh and sweet', 7, 'TeaMaster', 19.99, 15.99, 'USD', 6.00, 1000, 100, '{"weight_g":100,"type":"green_tea","organic":true,"origin":"China"}', 'https://images.example.com/green-tea.jpg', 'GLOBAL', '09021000', 'active', 4),
('SKU-EL-002', '机械键盘 RGB', 'Mechanical Keyboard RGB', 'Cherry MX轴体，全键RGB背光，铝合金面板', 'Cherry MX switches, per-key RGB, aluminum frame', 1, 'KeyMaster', 149.99, 129.99, 'USD', 65.00, 250, 25, '{"color":["black","white"],"switch_type":"Cherry MX Brown","layout":"US"}', 'https://images.example.com/mech-keyboard.jpg', 'GLOBAL', '84716000', 'active', 6),
('SKU-FS-006', '真皮手提包', 'Genuine Leather Handbag', '意大利进口头层牛皮，简约通勤设计', 'Italian imported top-grain leather, minimalist commuter design', 2, 'LuxeBag', 199.99, 169.99, 'USD', 75.00, 150, 15, '{"color":["black","brown","tan"],"material":"genuine_leather","size_cm":"30x22x12"}', 'https://images.example.com/leather-bag.jpg', 'US', '42022100', 'active', 2),
('SKU-BT-007', '平板电脑 11寸', 'Tablet 11 inch', '2K高清屏，8核处理器，支持手写笔', '2K display, octa-core processor, stylus support', 1, 'TabPro', 499.99, 449.99, 'USD', 280.00, 100, 10, '{"color":["silver","blue","pink"],"storage_gb":128,"ram_gb":8,"screen_size_inch":11}', 'https://images.example.com/tablet.jpg', 'GLOBAL', '84713000', 'active', 3),
('SKU-HM-002', '记忆棉枕头', 'Memory Foam Pillow', '人体工学设计，慢回弹记忆棉，缓解颈椎压力', 'Ergonomic design, slow rebound memory foam, cervical relief', 4, 'SleepWell', 49.99, 39.99, 'USD', 15.00, 500, 50, '{"color":["white"],"size_cm":"60x40x12","material":"memory_foam"}', 'https://images.example.com/pillow.jpg', 'GLOBAL', '94049000', 'active', 4),
('SKU-FS-007', '男士商务衬衫', 'Men Business Shirt', '免烫防皱面料，修身版型', 'Wrinkle-free non-iron fabric, slim fit', 2, 'StyleMe', 59.99, 44.99, 'USD', 16.00, 400, 40, '{"color":["white","blue","pink","striped"],"size":["S","M","L","XL","XXL"],"material":"cotton_blend"}', 'https://images.example.com/business-shirt.jpg', 'GLOBAL', '62052000', 'active', 2),
('SKU-FD-002', '猫粮 5kg', 'Premium Cat Food 5kg', '天然无谷配方，高蛋白低碳水', 'Natural grain-free formula, high protein low carb', 8, 'PetCare', 45.99, 39.99, 'USD', 18.00, 300, 30, '{"weight_kg":5,"type":"dry_food","flavor":"chicken","life_stage":"adult"}', 'https://images.example.com/cat-food.jpg', 'GLOBAL', '23091000', 'active', 5);

-- ============================================================
-- 5. 订单数据（10条）
-- ============================================================
INSERT INTO orders (order_number, user_id, status, payment_status, fulfillment_status, subtotal, discount_amount, tax_amount, shipping_amount, total_amount, shipping_address, shipping_method, tracking_number, ordered_at, paid_at, shipped_at, source) VALUES
('ORD-20260701-00001', 1, 'delivered', 'success', 'fulfilled', 159.99, 0.00, 13.60, 5.99, 179.58, '{"name":"Alice Wang","phone":"+1-415-111-0001","country":"US","state":"CA","city":"San Francisco","address":"456 Market St","postal_code":"94105"}', 'standard', 'TRK-US-001', '2026-07-01 10:30:00+00', '2026-07-01 10:31:00+00', '2026-07-02 09:00:00+00', 'web'),
('ORD-20260702-00002', 2, 'shipped', 'success', 'fulfilled', 349.99, 50.00, 25.50, 0.00, 325.49, '{"name":"Bob Zhang","phone":"+1-212-222-0002","country":"US","state":"NY","city":"New York","address":"789 Broadway","postal_code":"10003"}', 'express', 'TRK-US-002', '2026-07-02 14:00:00+00', '2026-07-02 14:05:00+00', '2026-07-03 10:00:00+00', 'app'),
('ORD-20260703-00003', 3, 'processing', 'success', 'unfulfilled', 129.99, 0.00, 11.04, 4.99, 146.02, '{"name":"Cathy Li","phone":"+44-20-333-0003","country":"UK","city":"London","address":"10 Oxford St","postal_code":"W1D 1BS"}', 'standard', NULL, '2026-07-03 09:00:00+00', '2026-07-03 09:02:00+00', NULL, 'web'),
('ORD-20260704-00004', 4, 'confirmed', 'pending', 'unfulfilled', 299.99, 0.00, 39.00, 0.00, 338.99, '{"name":"David Chen","phone":"+86-138-444-0004","country":"CN","city":"Shanghai","address":"上海市浦东新区陆家嘴环路1000号","postal_code":"200120"}', 'express', NULL, '2026-07-04 16:00:00+00', NULL, NULL, 'app'),
('ORD-20260705-00005', 5, 'delivered', 'success', 'fulfilled', 69.99, 10.00, 5.10, 3.99, 69.08, '{"name":"Emma Liu","phone":"+1-310-555-0005","country":"US","state":"CA","city":"Los Angeles","address":"2000 Sunset Blvd","postal_code":"90028"}', 'standard', 'TRK-US-003', '2026-07-05 11:00:00+00', '2026-07-05 11:01:00+00', '2026-07-06 08:00:00+00', 'web'),
('ORD-20260706-00006', 6, 'shipped', 'success', 'fulfilled', 199.99, 0.00, 38.00, 15.00, 252.99, '{"name":"Frank Wu","phone":"+49-30-666-0006","country":"DE","city":"Berlin","address":"Friedrichstraße 100","postal_code":"10117"}', 'express', 'TRK-DE-001', '2026-07-06 12:00:00+00', '2026-07-06 12:03:00+00', '2026-07-07 09:00:00+00', 'web'),
('ORD-20260707-00007', 7, 'pending', 'pending', 'unfulfilled', 124.99, 0.00, 0.00, 8.00, 132.99, '{"name":"Grace Yang","phone":"+81-3-777-0007","country":"JP","city":"Tokyo","address":"東京都渋谷区神宮前1-2-3","postal_code":"150-0001"}', 'standard', NULL, '2026-07-07 08:00:00+00', NULL, NULL, 'app'),
('ORD-20260708-00008', 8, 'cancelled', 'refunded', 'unfulfilled', 449.99, 0.00, 38.25, 0.00, 488.24, '{"name":"Henry Zhou","phone":"+1-650-888-0008","country":"US","state":"CA","city":"San Jose","address":"3000 Tech Dr","postal_code":"95110"}', 'express', NULL, '2026-07-08 10:00:00+00', '2026-07-08 10:01:00+00', NULL, 'web'),
('ORD-20260709-00009', 9, 'delivered', 'success', 'fulfilled', 199.99, 28.00, 14.62, 0.00, 186.61, '{"name":"Ivy Sun","phone":"+86-139-999-0009","country":"CN","city":"Chengdu","address":"成都市高新区天府大道2000号","postal_code":"610041"}', 'express', 'TRK-CN-001', '2026-07-09 09:00:00+00', '2026-07-09 09:01:00+00', '2026-07-10 08:00:00+00', 'app'),
('ORD-20260710-00010', 10, 'confirmed', 'success', 'unfulfilled', 39.99, 0.00, 3.40, 4.99, 48.38, '{"name":"Jack Ma","phone":"+1-408-101-0010","country":"US","state":"WA","city":"Seattle","address":"500 Pine St","postal_code":"98101"}', 'standard', NULL, '2026-07-10 15:00:00+00', '2026-07-10 15:02:00+00', NULL, 'web');

-- ============================================================
-- 6. 订单明细数据
-- ============================================================
INSERT INTO order_items (order_id, product_id, product_name, product_sku, product_image, quantity, unit_price) VALUES
(1, 1, '蓝牙降噪耳机 Pro', 'SKU-BT-001', 'https://images.example.com/bt-headphone-pro.jpg', 1, 159.99),
(2, 5, '智能手表 Ultra', 'SKU-BT-003', 'https://images.example.com/smart-watch.jpg', 1, 299.99),
(3, 4, '男士运动跑鞋', 'SKU-FS-002', 'https://images.example.com/running-shoes.jpg', 1, 99.99),
(3, 2, '无线充电器 15W', 'SKU-BT-002', 'https://images.example.com/wireless-charger.jpg', 1, 24.99),
(4, 5, '智能手表 Ultra', 'SKU-BT-003', 'https://images.example.com/smart-watch.jpg', 1, 299.99),
(5, 3, '女士夏季连衣裙', 'SKU-FS-001', 'https://images.example.com/summer-dress.jpg', 1, 49.99),
(5, 9, '防晒霜 SPF50+', 'SKU-FS-003', 'https://images.example.com/sunscreen.jpg', 1, 19.99),
(6, 16, '真皮手提包', 'SKU-FS-006', 'https://images.example.com/leather-bag.jpg', 1, 169.99),
(7, 10, '精华液 - 玻尿酸保湿', 'SKU-FS-004', 'https://images.example.com/serum.jpg', 2, 29.99),
(7, 9, '防晒霜 SPF50+', 'SKU-FS-003', 'https://images.example.com/sunscreen.jpg', 1, 19.99),
(8, 17, '平板电脑 11寸', 'SKU-BT-007', 'https://images.example.com/tablet.jpg', 1, 449.99),
(9, 16, '真皮手提包', 'SKU-FS-006', 'https://images.example.com/leather-bag.jpg', 1, 169.99),
(9, 10, '精华液 - 玻尿酸保湿', 'SKU-FS-004', 'https://images.example.com/serum.jpg', 1, 29.99),
(10, 20, '猫粮 5kg', 'SKU-FD-002', 'https://images.example.com/cat-food.jpg', 1, 39.99);

-- ============================================================
-- 7. 支付数据
-- ============================================================
INSERT INTO payments (transaction_id, order_id, user_id, amount, currency, status, method, gateway, paid_at) VALUES
('TXN-20260701-001', 1, 1, 179.58, 'USD', 'success', 'credit_card', 'stripe', '2026-07-01 10:31:00+00'),
('TXN-20260702-002', 2, 2, 325.49, 'USD', 'success', 'paypal', 'paypal', '2026-07-02 14:05:00+00'),
('TXN-20260703-003', 3, 3, 146.02, 'USD', 'success', 'credit_card', 'stripe', '2026-07-03 09:02:00+00'),
('TXN-20260704-004', 4, 4, 338.99, 'USD', 'pending', 'alipay', 'alipay', NULL),
('TXN-20260705-005', 5, 5, 69.08, 'USD', 'success', 'credit_card', 'stripe', '2026-07-05 11:01:00+00'),
('TXN-20260706-006', 6, 6, 252.99, 'USD', 'success', 'paypal', 'paypal', '2026-07-06 12:03:00+00'),
('TXN-20260707-007', 7, 7, 132.99, 'USD', 'pending', 'credit_card', 'stripe', NULL),
('TXN-20260708-008', 8, 8, 488.24, 'USD', 'refunded', 'credit_card', 'stripe', '2026-07-08 10:01:00+00'),
('TXN-20260709-009', 9, 9, 186.61, 'USD', 'success', 'wechat_pay', 'wechat', '2026-07-09 09:01:00+00'),
('TXN-20260710-010', 10, 10, 48.38, 'USD', 'success', 'credit_card', 'stripe', '2026-07-10 15:02:00+00');

-- 退款记录
UPDATE payments SET refund_amount = 488.24, refund_reason = '用户取消订单', refunded_at = '2026-07-09 08:00:00+00' WHERE transaction_id = 'TXN-20260708-008';

-- ============================================================
-- 8. 物流数据
-- ============================================================
INSERT INTO logistics (order_id, user_id, tracking_number, carrier, carrier_code, status, current_location, origin_address, destination_address, estimated_delivery_date, actual_delivery_date, shipped_at, delivered_at, shipping_cost, weight_kg) VALUES
(1, 1, 'TRK-US-001', 'FedEx', 'fedex', 'delivered', 'San Francisco, CA', '{"country":"CN","city":"Shenzhen"}', '{"country":"US","state":"CA","city":"San Francisco"}', '2026-07-08', '2026-07-07', '2026-07-02 09:00:00+00', '2026-07-07 14:00:00+00', 5.99, 0.35),
(2, 2, 'TRK-US-002', 'UPS', 'ups', 'delivered', 'New York, NY', '{"country":"CN","city":"Shenzhen"}', '{"country":"US","state":"NY","city":"New York"}', '2026-07-10', '2026-07-09', '2026-07-03 10:00:00+00', '2026-07-09 16:00:00+00', 0.00, 0.15),
(5, 5, 'TRK-US-003', 'USPS', 'usps', 'delivered', 'Los Angeles, CA', '{"country":"US","state":"CA","city":"Los Angeles"}', '{"country":"US","state":"CA","city":"Los Angeles"}', '2026-07-08', '2026-07-07', '2026-07-06 08:00:00+00', '2026-07-07 12:00:00+00', 3.99, 0.55),
(6, 6, 'TRK-DE-001', 'DHL', 'dhl', 'in_transit', 'Frankfurt, DE', '{"country":"CN","city":"Shenzhen"}', '{"country":"DE","city":"Berlin"}', '2026-07-15', NULL, '2026-07-07 09:00:00+00', NULL, 15.00, 1.20),
(9, 9, 'TRK-CN-001', '顺丰速运', 'sf', 'delivered', '成都市', '{"country":"CN","city":"Shenzhen"}', '{"country":"CN","city":"Chengdu"}', '2026-07-12', '2026-07-11', '2026-07-10 08:00:00+00', '2026-07-11 10:00:00+00', 0.00, 0.80);

-- 物流追踪明细
INSERT INTO logistics_tracking_details (logistics_id, status, location, description, event_time) VALUES
(1, 'picked_up', '深圳', '包裹已揽收', '2026-07-02 10:00:00+00'),
(1, 'in_transit', '深圳海关', '清关完成', '2026-07-03 08:00:00+00'),
(1, 'in_transit', '洛杉矶', '抵达目的国', '2026-07-05 06:00:00+00'),
(1, 'out_for_delivery', '旧金山', '正在派送中', '2026-07-07 08:00:00+00'),
(1, 'delivered', '旧金山', '已签收', '2026-07-07 14:00:00+00'),
(2, 'picked_up', '深圳', '包裹已揽收', '2026-07-03 11:00:00+00'),
(2, 'in_transit', '香港', '转运中', '2026-07-04 06:00:00+00'),
(2, 'in_transit', '纽约', '抵达目的国', '2026-07-08 04:00:00+00'),
(2, 'out_for_delivery', '纽约', '正在派送中', '2026-07-09 07:00:00+00'),
(2, 'delivered', '纽约', '已签收', '2026-07-09 16:00:00+00'),
(4, 'picked_up', '深圳', '包裹已揽收', '2026-07-07 10:00:00+00'),
(4, 'in_transit', '深圳海关', '清关中', '2026-07-08 08:00:00+00'),
(4, 'in_transit', '法兰克福', '抵达目的国', '2026-07-12 05:00:00+00');

-- ============================================================
-- 9. 用户行为数据
-- ============================================================
INSERT INTO user_behaviors (user_id, session_id, behavior_type, page_url, product_id, duration_seconds, device_type, country, event_time) VALUES
(1, 'SESS-001', 'page_view', '/products/electronics', NULL, 120, 'mobile', 'US', '2026-07-01 10:00:00+00'),
(1, 'SESS-001', 'search', '/search?q=bluetooth+headphones', NULL, 30, 'mobile', 'US', '2026-07-01 10:02:00+00'),
(1, 'SESS-001', 'click', '/products/SKU-BT-001', 1, 180, 'mobile', 'US', '2026-07-01 10:05:00+00'),
(1, 'SESS-001', 'add_to_cart', '/cart', 1, 5, 'mobile', 'US', '2026-07-01 10:20:00+00'),
(1, 'SESS-001', 'purchase', '/checkout', 1, 60, 'mobile', 'US', '2026-07-01 10:30:00+00'),
(2, 'SESS-002', 'page_view', '/', NULL, 45, 'desktop', 'US', '2026-07-02 13:00:00+00'),
(2, 'SESS-002', 'click', '/products/smart-watches', NULL, 15, 'desktop', 'US', '2026-07-02 13:05:00+00'),
(2, 'SESS-002', 'click', '/products/SKU-BT-003', 5, 300, 'desktop', 'US', '2026-07-02 13:10:00+00'),
(2, 'SESS-002', 'add_to_cart', '/cart', 5, 3, 'desktop', 'US', '2026-07-02 13:55:00+00'),
(2, 'SESS-002', 'purchase', '/checkout', 5, 90, 'desktop', 'US', '2026-07-02 14:00:00+00'),
(3, 'SESS-003', 'page_view', '/products/fashion', NULL, 200, 'mobile', 'UK', '2026-07-03 08:00:00+00'),
(3, 'SESS-003', 'click', '/products/SKU-FS-001', 3, 90, 'mobile', 'UK', '2026-07-03 08:15:00+00'),
(3, 'SESS-003', 'click', '/products/SKU-FS-002', 4, 120, 'mobile', 'UK', '2026-07-03 08:25:00+00'),
(3, 'SESS-003', 'add_to_cart', '/cart', 4, 5, 'mobile', 'UK', '2026-07-03 08:55:00+00'),
(3, 'SESS-003', 'add_to_cart', '/cart', 2, 3, 'mobile', 'UK', '2026-07-03 08:56:00+00'),
(3, 'SESS-003', 'purchase', '/checkout', NULL, 120, 'mobile', 'UK', '2026-07-03 09:00:00+00'),
(5, 'SESS-004', 'page_view', '/products/beauty', NULL, 90, 'tablet', 'US', '2026-07-05 10:00:00+00'),
(5, 'SESS-004', 'click', '/products/SKU-FS-001', 3, 60, 'tablet', 'US', '2026-07-05 10:15:00+00'),
(5, 'SESS-004', 'click', '/products/SKU-FS-003', 9, 80, 'tablet', 'US', '2026-07-05 10:20:00+00'),
(5, 'SESS-004', 'add_to_cart', '/cart', 3, 3, 'tablet', 'US', '2026-07-05 10:50:00+00'),
(5, 'SESS-004', 'add_to_cart', '/cart', 9, 2, 'tablet', 'US', '2026-07-05 10:51:00+00'),
(5, 'SESS-004', 'purchase', '/checkout', NULL, 90, 'tablet', 'US', '2026-07-05 11:00:00+00');

-- ============================================================
-- 10. 库存数据
-- ============================================================
INSERT INTO inventory (product_id, warehouse_id, sku, quantity, reserved_quantity, safety_stock, reorder_point, warehouse_name, location_code, batch_number, unit_cost) VALUES
(1, 1, 'SKU-BT-001', 300, 5, 50, 100, '深圳主仓', 'A-01-01', 'BATCH-20260601', 85.00),
(1, 2, 'SKU-BT-001', 200, 2, 30, 60, '美国洛杉矶仓', 'B-02-03', 'BATCH-20260601', 85.00),
(2, 1, 'SKU-BT-002', 800, 10, 100, 200, '深圳主仓', 'A-01-02', 'BATCH-20260605', 8.50),
(2, 2, 'SKU-BT-002', 400, 0, 50, 100, '美国洛杉矶仓', 'B-02-04', 'BATCH-20260605', 8.50),
(3, 1, 'SKU-FS-001', 300, 3, 30, 60, '深圳主仓', 'A-02-01', 'BATCH-20260610', 18.00),
(4, 1, 'SKU-FS-002', 450, 5, 50, 80, '深圳主仓', 'A-02-02', 'BATCH-20260615', 42.00),
(5, 1, 'SKU-BT-003', 100, 2, 20, 40, '深圳主仓', 'A-01-03', 'BATCH-20260620', 150.00),
(5, 2, 'SKU-BT-003', 100, 0, 15, 30, '美国洛杉矶仓', 'B-02-05', 'BATCH-20260620', 150.00),
(6, 1, 'SKU-BT-004', 600, 0, 80, 150, '深圳主仓', 'A-01-04', 'BATCH-20260601', 15.00),
(6, 3, 'SKU-BT-004', 200, 0, 30, 60, '德国法兰克福仓', 'C-01-01', 'BATCH-20260601', 15.00),
(7, 1, 'SKU-BT-005', 400, 0, 60, 120, '深圳主仓', 'A-01-05', 'BATCH-20260605', 28.00),
(7, 2, 'SKU-BT-005', 200, 0, 30, 60, '美国洛杉矶仓', 'B-02-06', 'BATCH-20260605', 28.00),
(9, 1, 'SKU-FS-003', 1500, 0, 200, 400, '深圳主仓', 'A-03-01', 'BATCH-20260625', 7.00),
(9, 5, 'SKU-FS-003', 500, 0, 80, 150, '英国伦敦仓', 'E-01-01', 'BATCH-20260625', 7.00),
(10, 1, 'SKU-FS-004', 1000, 0, 150, 300, '深圳主仓', 'A-03-02', 'BATCH-20260620', 10.00),
(10, 4, 'SKU-FS-004', 500, 0, 80, 150, '日本东京仓', 'D-01-01', 'BATCH-20260620', 10.00),
(16, 1, 'SKU-FS-006', 150, 2, 15, 30, '深圳主仓', 'A-02-04', 'BATCH-20260615', 75.00),
(17, 1, 'SKU-BT-007', 100, 1, 10, 20, '深圳主仓', 'A-01-06', 'BATCH-20260630', 280.00),
(19, 1, 'SKU-FS-007', 400, 0, 40, 80, '深圳主仓', 'A-02-05', 'BATCH-20260610', 16.00),
(20, 1, 'SKU-FD-002', 300, 0, 30, 60, '深圳主仓', 'A-04-01', 'BATCH-20260701', 18.00);

-- 库存流水
INSERT INTO inventory_transactions (inventory_id, product_id, warehouse_id, action, quantity_change, quantity_before, quantity_after, reference_type, reference_id, note) VALUES
(1, 1, 1, 'inbound', 500, 0, 500, 'purchase_order', 'PO-20260601', '首次入库'),
(1, 1, 1, 'outbound', -5, 500, 495, 'order', 'ORD-20260701-00001', '订单出库'),
(2, 1, 2, 'inbound', 200, 0, 200, 'transfer', 'TRF-20260615', '从深圳仓调拨'),
(2, 1, 2, 'outbound', -2, 200, 198, 'order', 'ORD-20260702-00002', '订单出库'),
(5, 5, 1, 'inbound', 200, 0, 200, 'purchase_order', 'PO-20260620', '首次入库'),
(5, 5, 1, 'outbound', -2, 200, 198, 'order', 'ORD-20260704-00004', '订单出库');

-- ============================================================
-- 11. 营销活动数据
-- ============================================================
INSERT INTO marketing_campaigns (campaign_code, name, campaign_type, description, start_date, end_date, discount_rules, total_budget, used_budget, target_segments, status, total_orders, total_revenue, total_discount) VALUES
('CAMP-SUMMER-2026', '2026夏季大促', 'seasonal_promo', '全站夏季促销活动，全场满减+折扣', '2026-07-01 00:00:00+00', '2026-07-31 23:59:59+00', '{"type":"percentage","value":15,"max_discount":100,"min_order_amount":50}', 50000.00, 12000.00, '["all_users"]', 'active', 45, 85000.00, 12750.00),
('CAMP-NEW-2026', '新用户专享', 'new_user', '首次购物享8折优惠', '2026-06-01 00:00:00+00', '2026-12-31 23:59:59+00', '{"type":"percentage","value":20,"max_discount":50,"min_order_amount":0}', 20000.00, 3500.00, '["new_users"]', 'active', 28, 18000.00, 3600.00),
('CAMP-FLASH-0713', '限时闪购', 'flash_sale', '蓝牙耳机限时特价', '2026-07-13 10:00:00+00', '2026-07-13 22:00:00+00', '{"type":"fixed","value":40,"applicable_products":[1]}', 5000.00, 0.00, '["electronics_lovers"]', 'active', 0, 0.00, 0.00);

-- 优惠券
INSERT INTO coupons (coupon_code, campaign_id, discount_type, discount_value, min_order_amount, total_quantity, used_quantity, start_date, expiry_date) VALUES
('SUMMER15', 1, 'percentage', 15.00, 50.00, 1000, 85, '2026-07-01 00:00:00+00', '2026-07-31 23:59:59+00'),
('NEWUSER20', 2, 'percentage', 20.00, 0.00, 500, 42, '2026-06-01 00:00:00+00', '2026-12-31 23:59:59+00'),
('FREESHIP', 1, 'free_shipping', 0.00, 30.00, 500, 120, '2026-07-01 00:00:00+00', '2026-07-31 23:59:59+00'),
('FLASH40', 3, 'fixed_amount', 40.00, 0.00, 100, 0, '2026-07-13 10:00:00+00', '2026-07-13 22:00:00+00');

-- ============================================================
-- 12. 市场数据
-- ============================================================
INSERT INTO market_data (data_type, market, category, keyword, data_source, title, data_content, data_date) VALUES
('competitor', 'US', 'electronics', 'bluetooth headphones', 'amazon', '蓝牙耳机竞品分析', '{"bsr":1500,"avg_price":79.99,"price_range":{"min":19.99,"max":349.99},"top_brands":["Sony","Bose","Apple","AudioMax"],"monthly_search_volume":250000,"competitor_count":120,"avg_rating":4.2}', '2026-07-10'),
('trend', 'US', 'electronics', 'wireless earbuds', 'google_trends', '无线耳机趋势', '{"trend":"rising","growth_rate":0.15,"seasonality":"Q4_peak","interest_by_region":{"CA":85,"NY":78,"TX":72},"related_queries":["noise cancelling","gaming","sports"]}', '2026-07-10'),
('price', 'US', 'fashion', 'summer dress', 'amazon', '夏季连衣裙价格分析', '{"avg_price":45.50,"median_price":39.99,"price_distribution":{"0-25":0.15,"25-50":0.45,"50-100":0.30,"100+":0.10},"price_by_brand":{"Zara":49.99,"HM":34.99,"Uniqlo":29.99}}', '2026-07-09'),
('competitor', 'UK', 'beauty', 'sunscreen', 'amazon', '防晒霜英国市场', '{"bsr":800,"avg_price":18.99,"price_range":{"min":5.99,"max":45.99},"top_brands":["La Roche-Posay","Neutrogena","SkinGuard"],"monthly_search_volume":120000,"competitor_count":85}', '2026-07-08'),
('trend', 'GLOBAL', 'electronics', 'smart watch', 'google_trends', '智能手表全球趋势', '{"trend":"stable","growth_rate":0.08,"seasonality":"Q4_peak","top_markets":["US","CN","DE","JP","UK"],"related_queries":["fitness tracker","health monitor","ECG"]}', '2026-07-11'),
('ranking', 'US', 'electronics', 'tablet', 'amazon', '平板电脑排名', '{"top_products":[{"rank":1,"name":"iPad Pro","rating":4.8},{"rank":2,"name":"Samsung Galaxy Tab","rating":4.6},{"rank":3,"name":"TabPro 11","rating":4.5}],"category_sales_estimate":500000}', '2026-07-12');

-- ============================================================
-- 13. 广告计划数据
-- ============================================================
INSERT INTO advertising_plans (plan_code, name, platform, external_campaign_id, daily_budget, total_budget, spent_amount, start_date, end_date, targeting, creatives, product_ids, impressions, clicks, ctr, conversions, revenue, roas, status, generated_by) VALUES
('AD-GOOGLE-001', '蓝牙耳机-Google搜索广告', 'google', 'GA-20260701-001', 50.00, 1500.00, 320.00, '2026-07-01 00:00:00+00', '2026-07-31 23:59:59+00', '{"locations":["US","UK"],"languages":["en"],"keywords":["bluetooth headphones","wireless headphones","noise cancelling"]}', '[{"type":"text","headline":"Premium Noise Cancelling Headphones","description":"40hr battery life. Free shipping.","cta":"Shop Now"}]', '[1]', 50000, 1200, 0.0240, 45, 7200.00, 4.80, 'active', 'advertising'),
('AD-FB-001', '智能手表-Facebook广告', 'facebook', 'FB-20260705-001', 80.00, 2400.00, 450.00, '2026-07-05 00:00:00+00', '2026-07-25 23:59:59+00', '{"locations":["US","CA"],"age_range":[18,45],"interests":["fitness","technology","wearables"]}', '[{"type":"image","url":"https://images.example.com/ad-smartwatch.jpg","headline":"Track Your Fitness in Style","cta":"Learn More"}]', '[5]', 35000, 980, 0.0280, 38, 11400.00, 4.75, 'active', 'advertising'),
('AD-TT-001', '夏季连衣裙-TikTok广告', 'tiktok', 'TT-20260708-001', 30.00, 900.00, 120.00, '2026-07-08 00:00:00+00', '2026-07-20 23:59:59+00', '{"locations":["US","UK"],"age_range":[18,35],"interests":["fashion","shopping","lifestyle"],"gender":"female"}', '[{"type":"video","url":"https://videos.example.com/dress-ad.mp4","caption":"Summer vibes! #SummerFashion"}]', '[3]', 80000, 2400, 0.0300, 30, 1500.00, 1.67, 'active', 'advertising'),
('AD-AM-001', '真皮手提包-亚马逊广告', 'amazon', 'AM-20260710-001', 40.00, 1200.00, 0.00, '2026-07-15 00:00:00+00', '2026-08-15 23:59:59+00', '{"locations":["US"],"keywords":["leather handbag","designer bag","work bag","tote"]}', '[{"type":"sponsored_product","asin":"B0XXXXXXX"}]', '[16]', 0, 0, 0.0000, 0, 0.00, 0.0000, 'draft', 'advertising');

-- ============================================================
-- 14. 客服对话数据
-- ============================================================
INSERT INTO customer_service_conversations (conversation_id, user_id, subject, status, channel, order_id, intent, sentiment, priority, handled_by_agent, agent_name, started_at, resolved_at) VALUES
('a1b2c3d4-0001-4000-8000-000000000001', 1, '订单配送查询', 'resolved', 'chat', 1, 'order_query', 'neutral', 'normal', TRUE, 'customer_service', '2026-07-05 14:00:00+00', '2026-07-05 14:05:00+00'),
('a1b2c3d4-0002-4000-8000-000000000002', 3, '退货咨询', 'resolved', 'chat', 3, 'refund', 'negative', 'high', TRUE, 'customer_service', '2026-07-06 10:00:00+00', '2026-07-06 10:15:00+00'),
('a1b2c3d4-0003-4000-8000-000000000003', 8, '取消订单', 'resolved', 'chat', 8, 'refund', 'neutral', 'normal', TRUE, 'customer_service', '2026-07-08 09:00:00+00', '2026-07-08 09:10:00+00'),
('a1b2c3d4-0004-4000-8000-000000000004', 5, '产品咨询', 'resolved', 'chat', NULL, 'product_inquiry', 'positive', 'low', TRUE, 'customer_service', '2026-07-10 11:00:00+00', '2026-07-10 11:03:00+00'),
('a1b2c3d4-0005-4000-8000-000000000005', 7, '支付问题', 'active', 'chat', 7, 'order_query', 'negative', 'high', TRUE, 'customer_service', '2026-07-12 08:00:00+00', NULL);

-- 客服消息
INSERT INTO cs_messages (conversation_id, role, content, message_type, response_time_ms, created_at) VALUES
(1, 'user', '你好，我想查询我的订单 ORD-20260701-00001 的配送状态', 'text', NULL, '2026-07-05 14:00:00+00'),
(1, 'assistant', '您好 Alice！您的订单已在配送中，预计 7月7日送达。当前快递位置：旧金山配送站。', 'text', 1200, '2026-07-05 14:00:01+00'),
(1, 'user', '谢谢！', 'text', NULL, '2026-07-05 14:05:00+00'),
(1, 'assistant', '不客气！如有其他问题，随时联系我们。', 'text', 800, '2026-07-05 14:05:01+00'),
(2, 'user', '我收到的连衣裙颜色和图片不符，想退货退款', 'text', NULL, '2026-07-06 10:00:00+00'),
(2, 'assistant', '非常抱歉给您带来不便！我来帮您处理退货退款。请问您是否已拆封商品标签？', 'text', 1500, '2026-07-06 10:00:02+00'),
(2, 'user', '还没有，标签完好的', 'text', NULL, '2026-07-06 10:05:00+00'),
(2, 'assistant', '好的，我已为您创建退货申请 RMA-20260706-001。您将收到退货标签，退款将在收到退货后3-5个工作日内处理。', 'text', 2000, '2026-07-06 10:05:02+00'),
(3, 'user', '我想取消订单 ORD-20260708-00008', 'text', NULL, '2026-07-08 09:00:00+00'),
(3, 'assistant', '好的，您的订单已成功取消。退款 488.24 美元将在3-5个工作日内退回到您的信用卡。', 'text', 1000, '2026-07-08 09:00:01+00'),
(4, 'user', '这款防晒霜适合敏感肌吗？', 'text', NULL, '2026-07-10 11:00:00+00'),
(4, 'assistant', '是的！SkinGuard SPF50+ 防晒霜采用温和配方，不含酒精和香料，经皮肤科测试，适合所有肤质包括敏感肌。', 'text', 1800, '2026-07-10 11:00:02+00'),
(5, 'user', '我的订单 ORD-20260707-00007 支付一直显示 pending', 'text', NULL, '2026-07-12 08:00:00+00'),
(5, 'assistant', '我检查到您的支付正在处理中。可能是信用卡授权延迟，请稍等10-15分钟。如果问题持续，建议联系您的银行确认。', 'text', 2500, '2026-07-12 08:00:03+00');

-- ============================================================
-- 15. 供应链预测数据
-- ============================================================
INSERT INTO supply_chain_forecasts (product_id, warehouse_id, forecast_period_days, forecast_date, forecast_method, predicted_demand, confidence_lower, confidence_upper, confidence_level, actual_demand, recommended_reorder, recommended_safety_stock, lead_time_days, generated_by) VALUES
(1, 1, 30, '2026-07-01', 'arima', 350, 280, 420, 0.9500, NULL, 300, 80, 7, 'supply_chain'),
(1, 2, 30, '2026-07-01', 'arima', 200, 160, 240, 0.9500, NULL, 150, 50, 14, 'supply_chain'),
(5, 1, 30, '2026-07-01', 'prophet', 150, 120, 180, 0.9500, NULL, 120, 40, 7, 'supply_chain'),
(3, 1, 30, '2026-07-01', 'moving_average', 250, 200, 300, 0.9000, NULL, 200, 60, 10, 'supply_chain'),
(4, 1, 30, '2026-07-01', 'arima', 180, 150, 210, 0.9500, NULL, 150, 50, 7, 'supply_chain'),
(9, 1, 30, '2026-07-01', 'moving_average', 800, 650, 950, 0.9000, NULL, 600, 200, 5, 'supply_chain'),
(10, 1, 30, '2026-07-01', 'prophet', 600, 480, 720, 0.9500, NULL, 500, 150, 5, 'supply_chain'),
(16, 1, 30, '2026-07-01', 'arima', 80, 60, 100, 0.9500, NULL, 60, 20, 10, 'supply_chain');

-- ============================================================
-- 16. Agent 任务日志
-- ============================================================
INSERT INTO agent_task_logs (task_id, session_id, agent_name, agent_role, task_type, status, priority, input_data, output_data, react_steps, tool_calls, duration_ms, token_usage, llm_model, mcp_calls_count, started_at, completed_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'SESS-MAIN-001', 'market_research', 'market_research', '选品分析', 'success', 'normal', '{"query":"分析美国市场蓝牙耳机选品","market":"US"}', '{"selected_products":[{"name":"蓝牙降噪耳机 Pro","score":92}],"analysis_report":"..."}', '[{"step":1,"thought":"搜索竞品蓝牙耳机","action":"search_competitor_products","observation":"找到120个竞品","duration_ms":1200},{"step":2,"thought":"分析市场趋势","action":"analyze_market_trends","observation":"趋势上升15%","duration_ms":800}]', '[{"tool":"search_competitor_products","args":{"keywords":["bluetooth","headphones"],"market":"US"},"result":{"count":120},"duration_ms":1200,"success":true}]', 3500, '{"prompt_tokens":500,"completion_tokens":300}', 'gpt-4o', 3, '2026-07-10 09:00:00+00', '2026-07-10 09:00:04+00'),
('550e8400-e29b-41d4-a716-446655440002', 'SESS-MAIN-001', 'advertising', 'advertising', '广告计划生成', 'success', 'normal', '{"products":[{"id":1,"name":"蓝牙降噪耳机 Pro"}],"budget":1500}', '{"ad_plans":[{"platform":"google","budget":1500}],"roas":4.8}', '[{"step":1,"thought":"生成Google广告计划","action":"generate_ad_plan","observation":"计划已生成","duration_ms":1500}]', '[{"tool":"generate_ad_plan","args":{"products":[{"id":1}],"total_budget":1500},"result":{"plan":"Google搜索广告"},"duration_ms":1500,"success":true}]', 2500, '{"prompt_tokens":400,"completion_tokens":250}', 'gpt-4o', 1, '2026-07-10 09:05:00+00', '2026-07-10 09:05:03+00'),
('550e8400-e29b-41d4-a716-446655440003', 'SESS-MAIN-002', 'customer_service', 'customer_service', '客服回复', 'success', 'normal', '{"query":"我想查询订单配送状态","order_id":"ORD-20260701-00001"}', '{"generated_response":"您的订单已在配送中...","intent":"order_query"}', '[{"step":1,"thought":"查询订单状态","action":"lookup_order_status","observation":"订单在配送中","duration_ms":800}]', '[{"tool":"lookup_order_status","args":{"order_id":"ORD-20260701-00001"},"result":{"status":"shipped"},"duration_ms":800,"success":true}]', 1200, '{"prompt_tokens":300,"completion_tokens":150}', 'gpt-4o', 1, '2026-07-05 14:00:00+00', '2026-07-05 14:00:01+00'),
('550e8400-e29b-41d4-a716-446655440004', 'SESS-MAIN-003', 'supply_chain', 'supply_chain', '需求预测', 'success', 'normal', '{"product_ids":[1,5],"forecast_period_days":30}', '{"demand_forecast":{"1":350,"5":150},"replenishment_suggestions":[]}', '[{"step":1,"thought":"预测蓝牙耳机需求","action":"forecast_demand","observation":"预测350件","duration_ms":2000}]', '[{"tool":"forecast_demand","args":{"product_ids":[1,5],"forecast_period_days":30},"result":{"1":350,"5":150},"duration_ms":2000,"success":true}]', 3000, '{"prompt_tokens":350,"completion_tokens":200}', 'gpt-4o', 1, '2026-07-01 08:00:00+00', '2026-07-01 08:00:03+00'),
('550e8400-e29b-41d4-a716-446655440005', 'SESS-MAIN-004', 'recommendation', 'recommendation', '个性化推荐', 'success', 'normal', '{"user_id":1}', '{"recommended_products":[{"id":1,"reason":"基于您的浏览历史"}],"ranking_scores":[]}', '[{"step":1,"thought":"获取用户画像","action":"get_user_profile","observation":"用户偏好电子产品","duration_ms":500}]', '[{"tool":"get_user_profile","args":{"user_id":1},"result":{"preferences":{"categories":["electronics"]}},"duration_ms":500,"success":true}]', 1500, '{"prompt_tokens":250,"completion_tokens":150}', 'gpt-4o', 1, '2026-07-11 10:00:00+00', '2026-07-11 10:00:02+00'),
('550e8400-e29b-41d4-a716-446655440006', 'SESS-MAIN-005', 'user_behavior', 'user_behavior', '用户分群', 'success', 'normal', '{"segmentation_type":"rfm"}', '{"segments":[{"name":"高价值客户","count":3},{"name":"活跃客户","count":4}],"segment_analysis":{}}', '[{"step":1,"thought":"RFM分群分析","action":"segment_users","observation":"完成分群","duration_ms":1000}]', '[{"tool":"segment_users","args":{"segmentation_type":"rfm"},"result":{"segments":[]},"duration_ms":1000,"success":true}]', 1800, '{"prompt_tokens":200,"completion_tokens":100}', 'gpt-4o', 1, '2026-07-12 09:00:00+00', '2026-07-12 09:00:02+00');

-- ============================================================
-- 17. 向量知识库数据
-- ============================================================
INSERT INTO knowledge_base (doc_id, title, content, chunk_index, chunk_total, category, sub_category, tags, market, language, source_type, review_status, quality_score, valid_from) VALUES
('KB-FAQ-001', '退换货政策', '我们提供30天无理由退换货服务。商品必须保持原包装完整，标签未撕毁。退款将在收到退货后3-5个工作日内处理。国际订单退货运费由客户承担。', 0, 3, 'policy', 'returns', '["returns","refund","policy"]', 'GLOBAL', 'en', 'manual', 'approved', 0.95, '2026-01-01 00:00:00+00'),
('KB-FAQ-002', '退换货政策 - 国际订单', '国际订单的退换货请在收到商品后14天内发起。退货运费由客户承担，除非商品存在质量问题。退货地址：中国深圳市宝安区福永街道物流园A1 退货部。', 1, 3, 'policy', 'returns', '["returns","international","refund"]', 'GLOBAL', 'en', 'manual', 'approved', 0.95, '2026-01-01 00:00:00+00'),
('KB-FAQ-003', '配送时间说明', '标准配送：美国境内5-7个工作日；国际标准配送：10-15个工作日；国际快递：5-8个工作日。请注意清关可能导致额外延迟。', 0, 2, 'faq', 'shipping', '["shipping","delivery","time"]', 'GLOBAL', 'en', 'manual', 'approved', 0.90, '2026-01-01 00:00:00+00'),
('KB-FAQ-004', '配送费用说明', '美国境内订单满$50免运费，不满$50收取$5.99标准运费。国际订单运费根据目的地和重量计算，结账时显示。', 1, 2, 'faq', 'shipping', '["shipping","cost","free_shipping"]', 'GLOBAL', 'en', 'manual', 'approved', 0.90, '2026-01-01 00:00:00+00'),
('KB-FAQ-005', '支付方式说明', '我们接受以下支付方式：Visa、Mastercard、American Express、PayPal、支付宝、微信支付。所有支付均通过SSL加密传输。', 0, 1, 'faq', 'payment', '["payment","methods","credit_card"]', 'GLOBAL', 'en', 'manual', 'approved', 0.92, '2026-01-01 00:00:00+00'),
('KB-PROD-001', '蓝牙降噪耳机 Pro 产品说明', '蓝牙降噪耳机 Pro 采用最新的主动降噪技术，可降低98%环境噪音。支持蓝牙5.3协议，兼容iOS和Android设备。40小时超长续航，支持快充（充电10分钟使用3小时）。配备记忆海绵耳罩，长时间佩戴舒适。', 0, 2, 'product_manual', 'electronics', '["product","bluetooth","headphones","specs"]', 'GLOBAL', 'en', 'manual', 'approved', 0.98, '2026-06-01 00:00:00+00'),
('KB-PROD-002', '蓝牙降噪耳机 Pro 故障排除', '常见问题：1. 无法配对：确保耳机处于配对模式（长按电源键5秒直到蓝灯闪烁）。2. 降噪效果差：检查耳罩是否完全贴合耳朵。3. 充电问题：使用原装USB-C充电线，确保充电口清洁。', 1, 2, 'product_manual', 'electronics', '["troubleshooting","bluetooth","headphones"]', 'GLOBAL', 'en', 'manual', 'approved', 0.95, '2026-06-01 00:00:00+00'),
('KB-PROD-003', '智能手表 Ultra 使用指南', '首次使用：1. 长按侧键开机；2. 下载"TechWear"App；3. 扫码配对。功能介绍：心率监测、血氧检测、GPS运动追踪、睡眠分析、消息通知。防水等级：5ATM（50米），可游泳佩戴。', 0, 1, 'product_manual', 'electronics', '["product","smartwatch","guide"]', 'GLOBAL', 'en', 'manual', 'approved', 0.97, '2026-06-15 00:00:00+00'),
('KB-FAQ-006', '隐私政策摘要', '我们重视您的隐私。我们收集的信息仅用于订单处理和改善服务体验。我们不会向第三方出售您的个人信息。详细隐私政策请访问我们的网站。', 0, 1, 'policy', 'privacy', '["privacy","data","policy"]', 'GLOBAL', 'en', 'manual', 'approved', 0.93, '2026-01-01 00:00:00+00'),
('KB-FAQ-007', '防晒霜 SPF50+ 使用建议', '建议在日晒前15-20分钟涂抹。每2小时补涂一次，游泳或出汗后立即补涂。适合所有肤质，包括敏感肌。不含酒精、香料和对羟基苯甲酸酯。', 0, 1, 'product_manual', 'beauty', '["product","sunscreen","usage"]', 'GLOBAL', 'en', 'manual', 'approved', 0.94, '2026-06-20 00:00:00+00');

-- ============================================================
-- 完成
-- ============================================================
-- 更新序列值
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders));
SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items));
SELECT setval('payments_id_seq', (SELECT MAX(id) FROM payments));
SELECT setval('logistics_id_seq', (SELECT MAX(id) FROM logistics));
SELECT setval('logistics_tracking_details_id_seq', (SELECT MAX(id) FROM logistics_tracking_details));
SELECT setval('user_behaviors_id_seq', (SELECT MAX(id) FROM user_behaviors));
SELECT setval('inventory_id_seq', (SELECT MAX(id) FROM inventory));
SELECT setval('inventory_transactions_id_seq', (SELECT MAX(id) FROM inventory_transactions));
SELECT setval('marketing_campaigns_id_seq', (SELECT MAX(id) FROM marketing_campaigns));
SELECT setval('coupons_id_seq', (SELECT MAX(id) FROM coupons));
SELECT setval('market_data_id_seq', (SELECT MAX(id) FROM market_data));
SELECT setval('advertising_plans_id_seq', (SELECT MAX(id) FROM advertising_plans));
SELECT setval('customer_service_conversations_id_seq', (SELECT MAX(id) FROM customer_service_conversations));
SELECT setval('cs_messages_id_seq', (SELECT MAX(id) FROM cs_messages));
SELECT setval('supply_chain_forecasts_id_seq', (SELECT MAX(id) FROM supply_chain_forecasts));
SELECT setval('agent_task_logs_id_seq', (SELECT MAX(id) FROM agent_task_logs));
SELECT setval('knowledge_base_id_seq', (SELECT MAX(id) FROM knowledge_base));
SELECT setval('suppliers_id_seq', (SELECT MAX(id) FROM suppliers));
SELECT setval('warehouses_id_seq', (SELECT MAX(id) FROM warehouses));