import type { UserRole } from "./types";

export const STAFF_ROLES: UserRole[] = ["barber", "owner", "admin"];

export function isStaff(role: UserRole | undefined): boolean {
  return !!role && STAFF_ROLES.includes(role);
}

/** Where a user should land after auth, based on their role. */
export function homePathForRole(role: UserRole | undefined): string {
  return isStaff(role) ? "/dashboard" : "/flex";
}
