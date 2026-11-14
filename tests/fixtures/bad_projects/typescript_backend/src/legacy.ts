// TS-001: Excessive use of unsafe any
export function transformPayload(data: any): any {
    const raw: any = data;
    return raw;
}
