export interface StudentBase {
    id?: string;
    firstName: string;
    lastName: string;
    rfidUid?: string;
    classGroup: string;
    promotion: string;
    faceEnrolled?: boolean;
    rfidEnrolled?: boolean;
}

export interface StudentRead extends StudentBase {
    rfidScanned: boolean;
}

export interface StudentUpdate {
    firstName?: string;
    lastName?: string;
    classGroup?: string;
    rfidUid?: string;
    promotion?: string;
    faceEnrolled?: boolean;
    rfidEnrolled?: boolean;
}

export interface StudentOperationResponse {
    message: string;
    success: boolean;
}

export interface StudentsPage {
    items: StudentRead[];
    total_items: number;
    page: number;
    limit: number;
}