import { Shield } from "lucide-react";
import { rolePermissions } from "@/constants/rolePermissions";
import { UserRole } from "@/types/userTypes";

interface Props { role: UserRole; }

const RolePermissionsDisplay = ({ role }: Props) => {
  const permissions = rolePermissions[role] || [];
  return (
    <div className="border rounded-lg p-3 bg-gray-50 mt-2">
      <div className="flex items-center mb-2 text-xs font-medium">
        <Shield className="h-3.5 w-3.5 mr-1 text-[#1f3d7a]" />
        Permissions associées
      </div>
      <ul className="space-y-1 text-xs text-gray-600">
        {permissions.map((p, i) => (
          <li key={i} className="flex">
            <span className="mr-1">•</span>
            <div>
              <span className="font-medium">{p.name}</span>
              <p className="text-xs text-gray-500">{p.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RolePermissionsDisplay;