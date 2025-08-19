-- Integration seed data for end-to-end API tests
-- Current time reference: 2025-08-19 22:30:00

SET FOREIGN_KEY_CHECKS = 0;

-- Clean tables (child -> parent order)
DELETE FROM payment_refund;
DELETE FROM payment_log;
DELETE FROM shipment;
DELETE FROM notification;
DELETE FROM order_item;
DELETE FROM `order`;
DELETE FROM auction_deposit;
DELETE FROM bid;
DELETE FROM auction;
DELETE FROM product_image;
DELETE FROM product_tag;
DELETE FROM tag;
DELETE FROM product;
DELETE FROM popup_store;
DELETE FROM phone_verification;
DELETE FROM `user`;
DELETE FROM payment;

-- Optional: create story tables if not exist (not managed by ORM)
CREATE TABLE IF NOT EXISTS story (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(200) NOT NULL,
  content VARCHAR(1024) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS story_image (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  story_id BIGINT UNSIGNED NOT NULL,
  image_url VARCHAR(1024) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Ensure compatibility with app queries (column may be present depending on DDL origin)
-- Add is_sold column if missing (MySQL-compatible)
SET @add_col_sql = (
  SELECT IF(
    EXISTS(
      SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'product'
        AND COLUMN_NAME = 'is_sold'
    ),
    'SELECT 1',
    'ALTER TABLE product ADD COLUMN is_sold INT NOT NULL DEFAULT 0'
  )
);
PREPARE stmt FROM @add_col_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------
-- Users
-- ---------
INSERT INTO `user` (id, email, nickname, phone_number, profile_image_url, is_phone_verified, created_at, updated_at)
VALUES
  (1001, 'alice@example.com', 'Alice', '+821012345678', 'https://nafalmvp-users.s3.ap-northeast-2.amazonaws.com/profile-image/user-3.png', 1, '2025-08-10 09:00:00', '2025-08-19 21:00:00'),
  (1002, 'bob@example.com',   'Bob',   '+821055512345', 'https://nafalmvp-users.s3.ap-northeast-2.amazonaws.com/profile-image/user-3.png', 0, '2025-08-11 10:00:00', '2025-08-19 21:00:00'),
  (1003, 'carol@example.com', 'Carol', '+821077788899', 'https://nafalmvp-users.s3.ap-northeast-2.amazonaws.com/profile-image/user-3.png', 1, '2025-08-12 11:00:00', '2025-08-19 21:00:00');

-- Phone verification cases (one valid, one expired)
INSERT INTO phone_verification (id, phone_number, code6, expires_at, verified_at, created_at)
VALUES
  (30001, '+821055512345', '123456', '2025-08-19 22:40:00', NULL, '2025-08-19 22:25:00'),
  (30002, '+821012345678', '654321', '2025-08-19 22:00:00', NULL, '2025-08-19 21:50:00');

-- ---------
-- Stores
-- ---------
INSERT INTO popup_store (id, name, description, sales_description, image_url, starts_at, ends_at, created_at)
VALUES
  (2001, 'Nafal Select', '선별된 디자인 오브제', '한정 수량 판매', 'https://nafalmvp-popup-stores.s3.ap-northeast-2.amazonaws.com/store-10.png', '2025-08-15 09:00:00', '2025-09-30 23:59:59', '2025-08-15 09:00:00'),
  (2002, 'Design Pop', '감각적인 조명과 가구', '주말 특가 진행', 'https://nafalmvp-popup-stores.s3.ap-northeast-2.amazonaws.com/store-10.png', '2025-08-10 10:00:00', '2025-08-25 22:00:00', '2025-08-10 10:00:00'),
  (2003, 'Classic House', '빈티지 콜렉션', '리미티드 에디션', 'https://nafalmvp-popup-stores.s3.ap-northeast-2.amazonaws.com/store-10.png', '2025-08-18 09:00:00', '2025-09-10 21:00:00', '2025-08-18 09:00:00');

-- ---------
-- Tags
-- ---------
INSERT INTO tag (id, name) VALUES
  (1, '오브제'),
  (2, '가구'),
  (3, '빈티지');

-- ---------
-- Products
-- ---------
INSERT INTO product (
  id, popup_store_id, category, name, summary, description, material, place_of_use,
  width_cm, height_cm, tolerance_cm, edition_info, condition_note, price, stock,
  shipping_base_fee, shipping_free_threshold, shipping_extra_note, courier_name, is_active, created_at, updated_at
) VALUES
  (3001, 2001, 'FURNITURE', 'Oak Side Table', '오크 사이드 테이블', '천연 오크로 만든 사이드 테이블', 'Oak', 'Living Room', 45.00, 50.00, 0.50, '1st Edition', '미세 스크래치 존재 가능', 120000.00, 10, 2500, 30000, NULL, 'CJ대한통운', 1, '2025-08-18 11:00:00', '2025-08-19 20:00:00'),
  (3002, 2001, 'LIGHTING',  'Canvas Lamp',    '캔버스 램프', '부드러운 간접 조명', 'Fabric', 'Bedroom', 20.00, 35.00, 0.30, NULL, NULL, 80000.00, 5, 2500, 30000, NULL, 'CJ대한통운', 1, '2025-08-18 12:00:00', '2025-08-19 20:00:00'),
  (3003, 2002, 'DECOR',     'Vintage Clock',  '빈티지 탁상시계', '클래식한 무드의 시계', 'Metal', 'Study', 15.00, 25.00, 0.20, NULL, '약한 변색 있음', 150000.00, 3, 2500, 30000, NULL, 'CJ대한통운', 1, '2025-08-12 09:00:00', '2025-08-16 10:00:00'),
  (3004, 2003, 'CERAMIC',   'Ceramic Vase',   '세라믹 화병', '수공예 도자기 화병', 'Ceramic', 'Living Room', 12.00, 30.00, 0.20, NULL, NULL, 60000.00, 8, 2500, 30000, NULL, 'CJ대한통운', 1, '2025-08-19 09:30:00', '2025-08-19 21:00:00'),
  (3005, 2001, 'CHAIR',     'Sold Chair',     '판매완료 체어', '전시 상품', 'Wood', 'Studio', 40.00, 85.00, 0.50, NULL, NULL, 90000.00, 0, 2500, 30000, NULL, 'CJ대한통운', 1, '2025-08-10 09:30:00', '2025-08-18 22:00:00'),
  (3006, 2003, 'LIGHTING',  'NoBuyNow Lamp',  '즉시구매 없음', '런칭 기념 스페셜', 'Metal', 'Bedroom', 18.00, 28.00, 0.20, NULL, NULL, 70000.00, 4, 2500, 30000, NULL, 'CJ대한통운', 1, '2025-08-19 18:00:00', '2025-08-19 21:00:00');

-- Product images (use single placeholder URL as requested)
INSERT INTO product_image (id, product_id, image_type, image_url, sort_order) VALUES
  (41001, 3001, 'MAIN',   'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 0),
  (41002, 3001, 'DETAIL', 'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 1),
  (41003, 3001, 'DETAIL', 'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 2),
  (41004, 3002, 'MAIN',   'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 0),
  (41005, 3004, 'MAIN',   'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 0),
  (41006, 3005, 'MAIN',   'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 0),
  (41007, 3006, 'MAIN',   'https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png', 0);

-- Product tags (simple mapping)
INSERT INTO product_tag (product_id, tag_id) VALUES
  (3001, 2),
  (3003, 3);

-- ---------
-- Auctions
-- ---------
INSERT INTO auction (
  id, product_id, start_price, min_bid_price, buy_now_price, deposit_amount, starts_at, ends_at, status, created_at, updated_at
) VALUES
  (4001, 3001, 50000.00, 1000.00, 200000.00, 10000.00, '2025-08-19 10:00:00', '2025-08-20 23:59:59', 'RUNNING',   '2025-08-19 10:00:00', '2025-08-19 21:00:00'),
  (4002, 3002, 60000.00, 1000.00, NULL,      0.00,      '2025-08-19 23:00:00', '2025-08-21 21:00:00', 'SCHEDULED', '2025-08-19 21:00:00', '2025-08-19 21:00:00'),
  (4003, 3003, 70000.00, 2000.00, 180000.00, 0.00,      '2025-08-10 09:00:00', '2025-08-15 18:00:00', 'ENDED',     '2025-08-10 09:00:00', '2025-08-15 18:30:00'),
  (4004, 3004, 30000.00, 1000.00, 90000.00,  0.00,      '2025-08-19 08:00:00', '2025-08-19 23:00:00', 'RUNNING',   '2025-08-19 08:00:00', '2025-08-19 21:00:00'),
  (4005, 3006, 35000.00, 1000.00, NULL,      0.00,      '2025-08-19 09:00:00', '2025-08-21 22:00:00', 'RUNNING',   '2025-08-19 09:00:00', '2025-08-19 21:00:00');

-- Bids (cover ordering and multiple users)
INSERT INTO bid (id, auction_id, user_id, bid_order, amount, created_at) VALUES
  (50001, 4001, 1002, 1, 70000.00, '2025-08-19 12:00:00'),
  (50002, 4001, 1001, 2, 71000.00, '2025-08-19 12:05:00'),
  (50003, 4004, 1003, 1, 35000.00, '2025-08-19 20:00:00'),
  (50004, 4005, 1002, 1, 36000.00, '2025-08-19 20:10:00');

-- ---------
-- Orders and Payments (pre-seeded PAID order to test refunds, etc.)
-- ---------
INSERT INTO `order` (id, user_id, address_id, status, total_amount, shipping_fee, created_at, updated_at)
VALUES (5001, 1003, NULL, 'PAID', 150000, 0, '2025-08-19 12:30:00', '2025-08-19 12:35:00');

INSERT INTO order_item (id, order_id, product_id, quantity, unit_price, subtotal_amount)
VALUES (51001, 5001, 3003, 1, 150000.00, 150000.00);

-- Payments (one for order, one for deposit prepayment example)
INSERT INTO payment (id, order_id, user_id, provider, external_tid, amount, status, requested_at, paid_at, fail_reason)
VALUES
  (6001, 5001, 1003, 'dummy', NULL, 150000.00, 'PAID', '2025-08-19 12:31:00', '2025-08-19 12:32:00', NULL),
  (6003, NULL, 1002, 'dummy', NULL, 10000.00, 'PAID', '2025-08-19 11:59:00', '2025-08-19 12:00:00', NULL);

INSERT INTO payment_log (id, payment_id, provider, external_tid, amount, status, requested_at, paid_at, fail_reason, log_type, created_at)
VALUES
  (70001, 6001, 'dummy', NULL, 150000.00, 'PAID', '2025-08-19 12:31:00', '2025-08-19 12:32:00', NULL, 'REQUEST', '2025-08-19 12:32:00'),
  (70002, 6003, 'dummy', NULL, 10000.00,  'PAID', '2025-08-19 11:59:00', '2025-08-19 12:00:00', NULL, 'REQUEST', '2025-08-19 12:00:00');

-- Auction deposits (link to payment 6003)
INSERT INTO auction_deposit (id, auction_id, user_id, payment_id, amount, status, created_at)
VALUES (62001, 4001, 1002, 6003, 10000.00, 'PAID', '2025-08-19 12:00:00');

-- Shipment for the paid order
INSERT INTO shipment (id, order_id, courier_name, tracking_number, status, shipped_at, delivered_at)
VALUES (73001, 5001, 'CJ대한통운', '1234-5678-ABCD', 'IN_TRANSIT', '2025-08-19 18:00:00', NULL),
       (73002, 5001, 'CJ대한통운', '1234-5678-ABCD', 'DELIVERED', '2025-08-19 18:00:00', '2025-08-19 21:30:00');

-- Notifications (sample existing notification)
INSERT INTO notification (id, user_id, channel, template_code, title, body, metadata_json, sent_at, status)
VALUES (90001, 1001, 'PUSH', NULL, '환영합니다', '회원가입을 환영합니다.', NULL, '2025-08-19 12:00:00', 'SENT');

-- ---------
-- Stories
-- ---------
DELETE FROM story_image;
DELETE FROM story;
INSERT INTO story (id, user_id, product_id, title, content, created_at, updated_at)
VALUES
  (80001, 1001, 3001, '사이드 테이블에 대한 이야기', '디자인 선정 배경과 제작기', '2025-08-19 13:00:00', '2025-08-19 13:10:00');

INSERT INTO story_image (id, story_id, image_url, sort_order)
VALUES
  (81001, 80001, 'https://nafalmvp-stories.s3.ap-northeast-2.amazonaws.com/story-15-20250819132012.png', 0),
  (81002, 80001, 'https://nafalmvp-stories.s3.ap-northeast-2.amazonaws.com/story-15-20250819132012.png', 1);

SET FOREIGN_KEY_CHECKS = 1;












#     status        enum ('QUEUED', 'SENT', 'FAILED') default 'SENT'            not null comment '상태',
# enum -> varchar
alter table notification modify column status varchar(20) not null default 'SENT';