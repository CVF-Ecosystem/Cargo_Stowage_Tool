# VINAFCO 268 — Đánh giá gói bàn giao và chọn phần tích hợp

Status: ADMITTED_FOR_SELECTIVE_INTEGRATION

## Kết luận

Gói dùng được làm nguồn tham số và tài sản 3D minh họa. Tích hợp một chế độ VINAFCO 268 bên cạnh mẫu M1, giữ rules và cách dựng hàng hiện có. Không nhận toàn bộ các hướng dẫn trong gói thành quyền mở rộng project; phạm vi được chốt trong [SPEC](../specs/SCST_VINAFCO268.md) và [work order](../work_orders/SCST_VINAFCO268.md) theo yêu cầu trực tiếp của owner.

## Đối chiếu nguồn

Root xem bản scan PDF trang 1, 4, 5, 6. Kích thước lớn nhất 77,8 × 13,24m, cao mạn 5,2m; chiều dài/rộng thiết kế 74,94 × 12,9m là các trường riêng. Giấy ghi lượng hàng 3282,5 / 3517,5t, TTTP 3301 / 3536t. Trang5 ghi trực tiếp mớn SI/SII 4,60 / 4,85m, mạn khô 612 / 362mm. Ghép cặp tải theo thứ tự trình bày cần giữ nhãn diễn giải, không biến thành một bảng nguồn vốn không có.

Trang5 có điều kiện riêng đối với chở container (mớn không vượt4,17m và tuân thủ thông báo ổn định được thẩm định). Lượt này chỉ có bó thép synthetic, không mở container. Không xác minh hiệu lực pháp lý hiện tại hoặc suy kết luận đủ điều kiện khai thác từ bản scan.

Root kiểm lại manifest 16/16 file; chạy hàm validator đã đọc source bằng Python local. GLB: 31 mesh, 3506 tam giác; bbox thân khớp số nguồn trong sai số float32; boong không phủ kín lỗ hầm. Terra kiểm độc lập cấu trúc GLB, chuyển trục và vật liệu. Kết quả mới ở [source-asset-validation.json](SCST_VINAFCO268_EVIDENCE/source-asset-validation.json), không chỉ dựa báo cáo web agent.

## Lựa chọn tái sử dụng

| Thành phần | Quyết định | Điều chỉnh cần thiết |
|---|---|---|
| PDF đăng kiểm, scan và metadata chủ phương tiện | Giữ nguyên trong gói local, không đưa vào app/Git | Gói đầu vào bị loại khỏi Git bằng `.gitignore`; API không phục vụ PDF |
| JSON tham số | Trích chọn trường kỹ thuật sang profile backend | Bỏ URL thư viện cá nhân và phần nhận dạng chủ tàu; giữ hash nguồn, số theo hồ sơ/ước tính/null và ghi chú |
| GLB | Dùng lại nguyên tài sản | Nạp local, tịnh tiến về hệ viewer; thêm vật liệu mờ/ẩn vỏ và xử lý nạp lỗi |
| PNG sơ đồ/preview | Tham khảo kiểm trực quan | Không đọc số làm tròn trên ảnh thành input tính |
| Python dựng/render/check | Tham khảo phương pháp; validator dùng cho kiểm nguồn local | Không thêm numpy/matplotlib/Pillow vào dependency app chỉ để nạp GLB có sẵn |
| Công thức trong HANDOFF | Chỉ dùng phần đã có trong rules | Chưa thêm thủy tĩnh/ổn định/trọng tâm toàn tàu, planner hay persistence |

## Những chỗ phải sửa khi nối vào app

1. **Contract:** M1 chỉ nhận SYNTHETIC, source mới cần MIXED_REFERENCE và nhận dạng/case có kiểu. Backend ràng buộc kích thước/giới hạn từ profile; UI không tự xác nhận nguồn. Mẫu mặc định tiếp tục hoạt động.
2. **Đơn vị:** hầm rộng10,34375m không biểu diễn chính xác bằng integer mm. Dùng10343mm, giảm0,75mm và đặt giữa hầm gốc; mỗi phía lùi0,375mm. Chiều dài56405mm, cao5408mm. Giữ số gốc trong profile và hiện chuyển đổi.
3. **Tọa độ:** GLB đã Y-up; không xoay lại. Tịnh tiến(-0,9725,-0,832,0)m đưa tâm hầm/sàn về viewer. TrụcY local của cargo đi sang phải tàu, tương ứng +Z GLB; nguồn JSON dùngY về trái tàu. Kiểm actual world matrix, không chỉ ảnh.
4. **Mớn:** màu thân tách tại4,85m được bake trong asset. VR-SI cần marker đúng4,60m và nhãn màu cố định; không nội suy theo tổng hàng.
5. **Tải:** mức hàng3517,5t khác TTTP3536t; hạ giới hạn chuyến vẫn được, không nâng giới hạn nguồn. Giữ onboard và kiểm quan hệ; đổi case không được âm thầm xóa hàng/nháp.
6. **Ước tính:** số hầm, vị trí/kích thước hầm, cabin, tuyến hình và hình học trang bị chưa đo. Tải sàn và lightship giữnull, UI hiển thị chưa có dữ liệu. Giảm0,75mm là chuyển đơn vị bảo thủ, không chứng minh biên hầm thực.

## Phần tiếp theo

Worker triển khai sáu tiêu chí VF-01…VF-06; root review kỹ thuật và kiểm sản phẩm trước bàn giao. Việc dùng cho hầm thật, nghiệm thu nghiệp vụ và các phần M2/M3 còn lại vẫn cần checkpoint của chúng. Hướng hình tàu được làm sớm chỉ trong lát cắt owner vừa yêu cầu, không đổi thứ tự toàn bộ roadmap.
