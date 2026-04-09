# BỘ CÂU HỎI KIỂM THỬ RAG CHATBOT (TEST CASES)

Dưới đây là danh sách các câu hỏi từ Dễ đến Khó được thiết kế dựa trên dữ liệu thực tế trong hệ thống (Giá tập, PT, Điều khoản, Chính sách bảo mật, Danh sách chi nhánh). Bạn có thể dùng bộ câu hỏi này để copy-paste trực tiếp vào UI kiểm tra độ thông minh và chính xác của Bot.

---

## 🟢 Cấp độ 1: Câu hỏi dễ (Dạng truy xuất thông tin trực tiếp)
*Sinh ra để kiểm tra khả năng bắt Keyword cơ bản của Model.*

1. **Về thông tin chi nhánh:**
   - "Chi nhánh The New Gym Gò Vấp nằm ở địa chỉ nào?"
   - "Phòng tập ở quận Tân Phú tên là gì thế?"
   - "Hệ thống có chi nhánh nào ở Cần Thơ không?"

2. **Về giá tập gym & giá PT:**
   - "Báo giá gói tập tại chi nhánh Điện Biên Phủ."
   - "Gói PT Silver bao nhiêu tiền?"
   - "Trong gói PT Diamond thì được tập bao nhiêu buổi?"
   - "Giá tập 1 tháng ở chi nhánh Đà Nẵng là bao tiền?"

3. **Về chính sách cơ bản:**
   - "Độ tuổi tối thiểu để đăng ký tập tại The New Gym là bao nhiêu?"
   - "Gym có mở cửa xuyên tết không? Thời gian hoạt động như thế nào?"

---

## 🟡 Cấp độ 2: Câu hỏi trung bình (Dạng cần tổng hợp hoặc tìm kiếm chéo)
*Sinh ra để kiểm tra khả năng lấy (retrieve) nhiều chunk trong một lần hỏi.*

1. **Kết hợp địa điểm & chính sách:**
   - "Tôi muốn chuyển nhượng gói tập cho bạn tôi thì The New Gym có cho phép không? Có tốn phí gì không?"
   - "Nếu tôi đi công tác lâu ngày thì có được bảo lưu (đóng băng) gói tập không? Thủ tục như thế nào?"

2. **Câu hỏi về Thanh toán:**
   - "Nếu tôi dùng gói thanh toán tự động, thẻ bị lỗi không trừ tiền được thì gói tập của tôi có bị hủy không?"
   - "Có những hình thức thanh toán nào khi mua gói tập?"

3. **Phân biệt gói tập:**
   - "Tôi mua gói 1 tháng thanh toán tiền mặt ở Cần Thơ khác gì so với đóng tự động?"
   - "Chính sách hủy gói tập thanh toán tự động diễn ra như thế nào?"

---

## 🔴 Cấp độ 3: Câu hỏi khó (Dạng gài bẫy, viết tắt, ngữ cảnh phức tạp)
*Sinh ra để kiểm tra luồng chuẩn hóa chuỗi (Normalization) vừa được viết và cách LLM suy luận ngữ cảnh.*

1. **Test chữ thường / viết tắt (Normalization Fix):**
   - "giá pt ở chi nhánh hvt là bao nhiêu v"
   - "ở nct và nkkkn có gói tập 6 tháng ko"

2. **Dạng kết hợp Giá + Nội Quy:**
   - "Tôi đang dùng gói tập ở 1 chi nhánh bên Tân Mỹ (Nguyễn Thị Thập), nhưng giờ tôi muốn chuyển sang gói đi toàn hệ thống cùng PT Platinum thì tôi phải trả bao nhiêu tiền và cách nâng cấp ra sao?"
   - "Hôm qua tôi lỡ làm mất đồ trong tủ locker của chi nhánh Ung Văn Khiêm, phòng gym có đền bù cho tôi không?"

3. **Câu hỏi dạng phân tích quy định bảo mật:**
   - "The New Gym có chia sẻ thông tin cá nhân của tôi cho bên thứ 3 nào không? Trong trường hợp nào thì bị chia sẻ?"
   - "Nếu tôi muốn xóa tài khoản và yêu cầu gym xóa hết dữ liệu camera quay lại tôi thì có được không?"

4. **Trường hợp vi phạm:**
   - "Nếu tôi dẫn bạn vào tập ké bằng mã của tôi thì hình phạt của phòng gym là gì?"
   - "Tôi tập tạ xong rồi vứt đó không cất thì có bị sao không?"

---
💡 **Mẹo:**
- Để ý phần Nguồn Tham Khảo (Sources) bên dưới câu trả lời của Bot. Nếu Bot trả lời đúng nhưng trích dẫn nhầm nguồn (dù hiếm) thì cần điều chỉnh lại chunking. 
- Giới hạn Context đang được set là 6 chunks để tránh Model bị "ngợp" thông tin.
