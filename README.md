# VG 8000 CORE — DEV V7

Mã nguồn lấy từ bản thử 18000, đã tích hợp V7 ngày 14/10/2026. Chưa triển khai và chưa nghiệm thu V7 trên máy Local. Bản sắp hàng V5 có mã/tên NVGH đã được người dùng nghiệm thu riêng trên Local.

V7 sửa tính tiền bán/KM và làm tròn, kiểm tra thanh toán/khóa phiếu, giao dịch chốt nhóm và thu nợ, kiểm tra trả hàng và đường dẫn ảnh QR. Ba module chính: app/qtgh_stable.py, app/qtgh_v02.py, app/qtgh_qr_snapshot_v11.py.

## Phạm vi xuất bản

Không chứa database, dữ liệu khách hàng, tệp đính kèm, tài khoản demo, môi trường .venv hoặc báo cáo có dữ liệu nghiệp vụ. Các workbook nhị phân chưa được rà soát dữ liệu nên không đưa lên; danh sách trong SOURCE_EXPORT.json. Cần bổ sung các template đã được kiểm tra trước khi chạy đầy đủ chức năng nhập/xuất MISA.

Đây là snapshot nguồn để phát triển và review, không phải bộ triển khai tự động. Không chạy trực tiếp vào dữ liệu đang vận hành. Cần môi trường riêng, cấu hình tài khoản an toàn và chặn API/thanh toán thật khi thử. Launcher 18000 và QR DEMO của máy DEV nằm ngoài cây nguồn ứng dụng, không được mang kèm dữ liệu/đường dẫn máy vào repository.

## Bằng chứng và giới hạn

Bộ audit V7 trước tích hợp có 100 mục PASS; kiểm tra nền, cú pháp và hash ba tệp sau tích hợp vào bản thử đều PASS. Chưa nghiệm thu giao diện sau khởi động lại; chưa đối chiếu chứng từ MISA. Không sửa số tiền lịch sử. Quy tắc credit/offset và phân bổ mã giao dịch ngân hàng nhiều hóa đơn còn chờ xác nhận.

Trước cập nhật Local phải ghép với nguồn thực tế Local, kiểm thử lại, sao lưu mã và chờ nghiệm thu. Không dùng snapshot này ghi đè Local.
