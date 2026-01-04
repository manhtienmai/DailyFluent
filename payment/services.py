"""
Payment services for Bank transfer with QR code generation
"""
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse
from .models import Payment


class BankTransferService:
    """Service để xử lý chuyển khoản ngân hàng với QR code"""
    
    @staticmethod
    def get_bank_info() -> dict:
        """Lấy thông tin tài khoản ngân hàng"""
        return {
            'account_name': getattr(settings, 'BANK_ACCOUNT_NAME', 'CONG TY TNHH DAILYFLUENT'),
            'account_number': getattr(settings, 'BANK_ACCOUNT_NUMBER', ''),
            'bank_name': getattr(settings, 'BANK_NAME', 'Vietcombank'),
            'branch': getattr(settings, 'BANK_BRANCH', ''),
        }
    
    @staticmethod
    def generate_qr_code(payment: Payment) -> bytes:
        """
        Tạo QR code cho chuyển khoản ngân hàng
        Format: VietQR hoặc format đơn giản với thông tin cần thiết
        """
        bank_info = BankTransferService.get_bank_info()
        
        # Tạo nội dung chuyển khoản (dùng payment ID để phân loại)
        # Format: Số tiền + Payment ID (8 ký tự đầu) + User ID
        transfer_content = f"{payment.id.hex[:8].upper()}"
        
        # Tạo QR data theo format VietQR (nếu hỗ trợ) hoặc format đơn giản
        # Format đơn giản: bank_account|account_name|amount|content
        qr_data = f"{bank_info['account_number']}|{bank_info['account_name']}|{int(payment.amount)}|{transfer_content}"
        
        # Hoặc có thể dùng format JSON cho dễ parse
        # qr_data = json.dumps({
        #     'account': bank_info['account_number'],
        #     'name': bank_info['account_name'],
        #     'amount': int(payment.amount),
        #     'content': transfer_content
        # })
        
        # Tạo QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Tạo image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
    
    @staticmethod
    def get_qr_code_image_response(payment: Payment) -> HttpResponse:
        """Trả về QR code image dưới dạng HTTP response"""
        qr_image = BankTransferService.generate_qr_code(payment)
        return HttpResponse(qr_image, content_type='image/png')
    
    @staticmethod
    def get_transfer_content(payment: Payment) -> str:
        """Lấy nội dung chuyển khoản để hiển thị cho user"""
        # Dùng 8 ký tự đầu của payment ID để dễ nhận biết
        return f"{payment.id.hex[:8].upper()}"
    
    @staticmethod
    def verify_bank_transfer(payment: Payment, transfer_code: str, image=None) -> dict:
        """Xác thực chuyển khoản ngân hàng (manual verification)"""
        payment.bank_transfer_code = transfer_code
        if image:
            payment.bank_transfer_image = image
        payment.status = Payment.PaymentStatus.PROCESSING
        payment.save()
        
        return {
            'success': True,
            'message': 'Thông tin chuyển khoản đã được gửi. Chúng tôi sẽ xác thực trong vòng 24 giờ.'
        }
