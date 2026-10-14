TEMPLATES = {
    "dms-xa": {
        "version": "VG-TPL-DMS-XA-V1.0",
        "filename": "01_Template_DMS_Xa_V1.0.xlsx",
        "sheets": {
            "CHI_TIET_XA": [
                ("NGAY_DON", True, "date"), ("MA_DON_DMS", True, "text"),
                ("MA_NV_NGHIEP_VU", True, "text"), ("MA_KH_DMS", False, "text"),
                ("MA_SKU", True, "text"), ("TEN_SKU", False, "text"),
                ("SL_SU", True, "number"), ("SL_THUNG", True, "number"),
                ("SL_KM_SU", True, "number"), ("SL_KM_THUNG", True, "number"),
                ("DON_GIA_CHUA_VAT", True, "number"), ("VAT_RATE", False, "number"),
                ("DOANH_SO_DMS", False, "number"), ("CK_KM_TIEN", True, "number"),
                ("GIAM_TRU_DONG_KHAC", True, "number"),
            ],
            "THUONG_CAP_DON": [
                ("MA_DON_DMS", True, "text"), ("NGAY_DON", True, "date"),
                ("MA_NV_NGHIEP_VU", True, "text"), ("THUONG_TRUNG_BAY", True, "number"),
                ("THUONG_TICH_LUY", True, "number"), ("GIAM_TRU_CAP_DON_KHAC", True, "number"),
            ],
        },
    },
    "dms-mbw": {
        "version": "VG-TPL-DMS-MBW-V1.0",
        "filename": "02_Template_DMS_MBW_GiaoThat_BanBu_V1.0.xlsx",
        "sheets": {"DU_LIEU": [
            ("NGAY_DON", True, "date"), ("NGAY_GIAO", False, "date"), ("MA_SKU", True, "text"),
            ("TEN_SKU", False, "text"), ("MA_NV_KD_NGHIEP_VU", True, "text"),
            ("SO_HOA_DON", True, "text"), ("DOANH_SO_PHAI_THU", False, "number"),
            ("MA_KH_NGUON", True, "text"), ("SL_SU", True, "number"), ("SL_KM_THUNG", True, "number"),
            ("SL_THUNG", True, "number"), ("DON_GIA_CHUA_VAT", True, "number"), ("SL_KM_SU", True, "number"),
            ("PHUONG_TIEN", False, "text"), ("LOAI_DON", True, "enum:L|B"),
            ("MA_NV_GIAO_HANG_NGHIEP_VU", False, "text"), ("MA_NV_LAI_XE_NGHIEP_VU", False, "text"),
            ("LO_GIAO_HANG", False, "text"),
        ]},
    },
    "misa-ban-bu": {
        "version": "VG-TPL-MISA-BANBU-V1.0",
        "filename": "03_Template_MISA_BanBu_V1.0.xlsx",
        "sheets": {"DU_LIEU": [
            ("NGAY_CHUNG_TU", True, "date"), ("SO_CHUNG_TU", True, "text"),
            ("MA_NV_NGHIEP_VU", True, "text"), ("MA_SKU", True, "text"), ("TEN_SKU", False, "text"),
            ("MA_KH_NGUON", False, "text"), ("TONG_SL_BAN", True, "number"), ("TONG_SL_TRA_LAI", True, "number"),
            ("DON_GIA_CHUA_VAT", True, "number"), ("VAT_RATE", False, "number"), ("CHIET_KHAU", True, "number"),
            ("GIA_TRI_GIAM_GIA", True, "number"), ("GIA_TRI_TRA_LAI", True, "number"),
        ]},
    },
    "misa-boc-vao": {
        "version": "VG-TPL-MISA-BOCVAO-V1.0",
        "filename": "04_Template_MISA_NhapHang_BocVao_V1.0.xlsx",
        "sheets": {"DU_LIEU": [
            ("NGAY_CHUNG_TU", True, "date"), ("SO_CHUNG_TU", True, "text"), ("MA_KHO", True, "text"),
            ("MA_DOI_TUONG", False, "text"), ("TEN_DOI_TUONG", False, "text"), ("MA_SKU", True, "text"),
            ("TEN_SKU", False, "text"), ("SL_SU", True, "number"), ("SL_THUNG", True, "number"),
            ("TINH_BOC_VAO", True, "enum:CO|KHONG"), ("GHI_CHU", False, "text"),
        ]},
    },
    "misa-boc-ra": {
        "version": "VG-TPL-MISA-BOCRA-V1.0",
        "filename": "05_Template_MISA_XuatBanBuon_BocRa_V1.0.xlsx",
        "sheets": {"DU_LIEU": [
            ("NGAY_CHUNG_TU", True, "date"), ("SO_CHUNG_TU", True, "text"), ("MA_KHO", True, "text"),
            ("MA_KH_NGUON", False, "text"), ("TEN_KH", False, "text"), ("MA_SKU", True, "text"),
            ("TEN_SKU", False, "text"), ("SL_SU", True, "number"), ("SL_THUNG", True, "number"),
            ("TINH_BOC_RA", True, "enum:CO|KHONG"), ("GHI_CHU", False, "text"),
        ]},
    },
}
