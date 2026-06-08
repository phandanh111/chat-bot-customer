# Test Cases — The New Gym Chatbot

Bộ test từ dễ đến khó, dựa trên dữ liệu thực tế trong document. Copy-paste thẳng vào UI để test.

---

## Level 1 — Factual Lookup (Truy xuất trực tiếp)

Bot chỉ cần tìm đúng 1 chunk và trả về thông tin.

| # | Câu hỏi | Kỳ vọng |
|---|---|---|
| TC-01 | Gym mở cửa mấy giờ? | Đa số chi nhánh 24/7. Riêng Cần Thơ 05:00–24:00 |
| TC-02 | Địa chỉ chi nhánh Quận 7 ở đâu? | 128 Đường Nguyễn Thị Thập, Bình Thuận, Q7 |
| TC-03 | Gói PT Gold giá bao nhiêu? | 4.999.000 VNĐ / 8 buổi |
| TC-04 | Số điện thoại hỗ trợ khách hàng là gì? | Hotline 1900 63 69 20, email cskh@thenewgym.vn |
| TC-05 | Gói PT Diamond bao nhiêu buổi? | 72 buổi / 28.200.000 VNĐ |
| TC-06 | Chi nhánh Gò Vấp tên đầy đủ là gì? | The New Gym Quang Trung, 185-189 Quang Trung, P.10, Gò Vấp |
| TC-07 | Giá tập ở Đà Nẵng bao nhiêu? | Tự động 249k/tháng, toàn hệ thống 399k/tháng |

---

## Level 2 — Câu hỏi ngắn / viết tắt (test Query Rewriting + Normalization)

Bot phải tự mở rộng câu hỏi trước khi tìm kiếm.

| # | Câu hỏi | Kỳ vọng |
|---|---|---|
| TC-08 | giá gym? | Liệt kê các gói từ 249k–399k theo nhóm chi nhánh |
| TC-09 | có pt không? | Giới thiệu 4 gói PT: Silver / Gold / Platinum / Diamond |
| TC-10 | giá pt ở hvt bao nhiêu? | Nhận ra hvt = Hoàng Văn Thụ. Giá PT áp dụng thống nhất toàn hệ thống |
| TC-11 | ở nct và pdl có gói 6 tháng ko | Nhận ra nct = Nguyễn Chí Thanh, pdl = Phan Đăng Lưu. Kiểm tra document có gói 6 tháng không |
| TC-12 | phí tập ở đây bao nhiêu vậy | Cần hỏi lại khu vực hoặc trả về bảng giá tổng quát |

---

## Level 3 — Tổng hợp nhiều chunk (test Reranking)

Bot cần kết hợp thông tin từ nhiều section document.

| # | Câu hỏi | Kỳ vọng |
|---|---|---|
| TC-13 | Nên chọn gói PT Platinum hay Diamond? Khác nhau chỗ nào? | Platinum: 12tr/24 buổi (~500k/buổi). Diamond: 28.2tr/72 buổi (~392k/buổi). Diamond tiết kiệm hơn theo buổi |
| TC-14 | Con tôi 13 tuổi có đăng ký tập được không? | Dưới 15 tuổi phải đăng ký kèm HLV cá nhân (PT) |
| TC-15 | Nếu thẻ thanh toán tự động bị lỗi thì gói tập có bị hủy không? | Hệ thống thử lần 2 vào ngày hết hạn. Sau 2 lần thất bại mới hủy |
| TC-16 | Tôi muốn hủy gói tập thì làm sao? | Đến chi nhánh 06:00–22:00. Mới đăng ký: hủy sau 14 ngày. Hủy trước 4 ngày hết hạn: hủy ngay. Hủy trong 3 ngày cuối: gia hạn thêm 1 tháng |
| TC-17 | Bị ốm có bảo lưu gói tập được không? | Có, tối đa 1 tháng mỗi lần. Hết hạn bảo lưu tự động kích hoạt lại |
| TC-18 | The New Gym có chia sẻ thông tin cá nhân của tôi không? | Chỉ chia sẻ với công ty con trong hệ sinh thái hoặc khi được người dùng cho phép. Không bán cho bên ngoài |

---

## Level 4 — Location-based (test Map Service + Static Coords)

Bot cần phát hiện location → gợi ý chi nhánh theo khoảng cách.

| # | Câu hỏi | Kỳ vọng |
|---|---|---|
| TC-19 | Tôi ở Quận 7, chi nhánh nào gần nhất? | The New Gym Nguyễn Thị Thập (Q7) gần nhất, kèm khoảng cách km |
| TC-20 | Nhà tôi ở Gò Vấp thì vô chỗ nào? | The New Gym Quang Trung (Gò Vấp) là gần nhất |
| TC-21 | Gần Bình Thạnh có chi nhánh nào không? | The New Gym Ung Văn Khiêm (Bình Thạnh) gần nhất |
| TC-22 | Tôi đang ở Biên Hòa, có chi nhánh nào không? | The New Gym Đồng Nai, 316 Nguyễn Ái Quốc, Biên Hòa |
| TC-23 | Tôi ở Quận 10, đi chi nhánh nào tiện nhất? | Điện Biên Phủ (Q10) hoặc Nguyễn Chí Thanh (Q10), cả 2 đều ở Q10 |

---

## Level 5 — Multi-turn Conversation (test Chat History)

Chạy từng lượt theo thứ tự trong cùng 1 cửa sổ chat.

**Kịch bản A — Follow-up**

> **Lượt 1:** Gói PT Gold gồm những gì?
>
> **Lượt 2:** Thế còn Platinum thì sao?
>
> **Lượt 3:** Cái nào tính ra rẻ hơn theo buổi?

**Kỳ vọng:** Bot nhớ context, không hỏi lại. Lượt 3 so sánh được Gold (~625k/buổi) vs Platinum (~500k/buổi).

---

**Kịch bản B — Đổi chủ đề rồi quay lại**

> **Lượt 1:** Chi nhánh Quận 5 ở đâu?
>
> **Lượt 2:** Giờ mở cửa ở đó thế nào?
>
> **Lượt 3:** Giá tập tại chi nhánh đó bao nhiêu?

**Kỳ vọng:** "ở đó" và "chi nhánh đó" đều được hiểu là Lê Hồng Phong (Q5). Trả lời đúng 24/7 và giá nhóm LHP.

---

**Kịch bản C — Quyết định mua**

> **Lượt 1:** Có mấy loại gói tập?
>
> **Lượt 2:** Tôi hay đi công tác nhiều tỉnh, nên chọn gói nào?
>
> **Lượt 3:** Giá bao nhiêu và đăng ký ở đâu?

**Kỳ vọng:** Lượt 2 bot gợi ý gói toàn hệ thống 399k. Lượt 3 cung cấp giá và hướng dẫn.

---

## Level 6 — Hallucination Guard (test Score Threshold)

Bot phải từ chối hoặc chuyển hướng, tuyệt đối không bịa thông tin.

| # | Câu hỏi | Kỳ vọng |
|---|---|---|
| TC-24 | The New Gym có hồ bơi không? | Không có thông tin. Đề nghị liên hệ hotline/Fanpage |
| TC-25 | Nghe nói gói tập chỉ 199k/tháng phải không? | Sửa lại: giá thấp nhất là 249k (nhóm tỉnh). Không xác nhận thông tin sai |
| TC-26 | Hôm nay thời tiết Hà Nội thế nào? | Từ chối lịch sự, chỉ hỗ trợ thông tin The New Gym |
| TC-27 | The New Gym có chi nhánh ở Hà Nội không? | Chưa có ở Hà Nội. Gợi ý các tỉnh đang có: HCM, Đồng Nai, Đà Nẵng, Cần Thơ |
| TC-28 | Tôi muốn xóa dữ liệu camera quay tôi thì có được không? | Camera CCTV có thể cung cấp cho cơ quan có thẩm quyền theo pháp luật. Bot không cam kết xóa |

---

## Level 7 — Edge Cases / Gài bẫy

| # | Câu hỏi | Điểm kiểm tra |
|---|---|---|
| TC-29 | Tôi muốn cho bạn mượn thẻ tập của tôi thì được không? | Không được — mỗi tài khoản chỉ dùng cho 1 hội viên, vi phạm có thể bị phạt hoặc hủy dịch vụ |
| TC-30 | Lỡ để đồ quên trong tủ locker qua đêm thì sao? | Sau 10h sáng hôm sau phá ổ khóa. Đồ chuyển vào khu thất lạc, giữ 1 tuần rồi quyên góp từ thiện |
| TC-31 | Tôi mang chó vào phòng tập được không? | Không được phép mang vật nuôi vào phòng tập |
| TC-32 | Lỡ đăng ký xong rồi đổi ý ngay hôm đó có hủy được không? | Không — gói thanh toán tự động chỉ hủy được sau 14 ngày kể từ ngày đăng ký |
| TC-33 | Tôi muốn nâng cấp từ gói 1 chi nhánh lên toàn hệ thống thì làm thế nào? | Nâng cấp qua app The New Gym bất cứ lúc nào. Gói mới có hiệu lực từ tháng tiếp theo |
| TC-34 | Gym có cho phép tập đấu võ trong phòng không? | Không — không được tập đấu bốc, võ thuật, thể thao tiếp xúc trừ khi có HLV được cấp phép |

---

## Checklist đánh giá sau khi test

| Tiêu chí | Test cases liên quan | Kết quả |
|---|---|---|
| Factual accuracy | TC-01 đến TC-07 | |
| Query rewriting hoạt động | TC-08 đến TC-12 | |
| Reranking lấy đúng context | TC-13 đến TC-18 | |
| Map Service đúng thứ tự gần-xa | TC-19 đến TC-23 | |
| Chat history được nhớ | Kịch bản A, B, C | |
| Không hallucinate | TC-24 đến TC-28 | |
| Edge cases xử lý đúng | TC-29 đến TC-34 | |
| Response speed (streaming mượt) | Tất cả | |
| Tiếng Việt tự nhiên | Tất cả | |
