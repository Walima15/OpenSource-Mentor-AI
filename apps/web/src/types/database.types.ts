// Generated from the Supabase schema via the Supabase MCP (do not edit by hand).
// Regenerate after schema changes with the `generate_typescript_types` MCP tool.

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      code_suggestions: {
        Row: {
          created_at: string | null
          diff: string | null
          explanation: string | null
          file_path: string
          id: string
          plan_id: string | null
          tests: string | null
        }
        Insert: {
          created_at?: string | null
          diff?: string | null
          explanation?: string | null
          file_path: string
          id?: string
          plan_id?: string | null
          tests?: string | null
        }
        Update: {
          created_at?: string | null
          diff?: string | null
          explanation?: string | null
          file_path?: string
          id?: string
          plan_id?: string | null
          tests?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "code_suggestions_plan_id_fkey"
            columns: ["plan_id"]
            isOneToOne: false
            referencedRelation: "contribution_plans"
            referencedColumns: ["id"]
          },
        ]
      }
      contribution_plans: {
        Row: {
          created_at: string
          id: string
          recommended_files: Json | null
          session_id: string | null
          status: Database["public"]["Enums"]["plan_status"]
          steps: Json | null
          summary: string | null
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: string
          recommended_files?: Json | null
          session_id?: string | null
          status?: Database["public"]["Enums"]["plan_status"]
          steps?: Json | null
          summary?: string | null
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          recommended_files?: Json | null
          session_id?: string | null
          status?: Database["public"]["Enums"]["plan_status"]
          steps?: Json | null
          summary?: string | null
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "contribution_plans_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "mentor_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      issues_cache: {
        Row: {
          fetched_at: string | null
          github_issue_number: number
          id: string
          labels: Json | null
          raw: Json | null
          repo_id: string | null
          state: string | null
          title: string
        }
        Insert: {
          fetched_at?: string | null
          github_issue_number: number
          id?: string
          labels?: Json | null
          raw?: Json | null
          repo_id?: string | null
          state?: string | null
          title: string
        }
        Update: {
          fetched_at?: string | null
          github_issue_number?: number
          id?: string
          labels?: Json | null
          raw?: Json | null
          repo_id?: string | null
          state?: string | null
          title?: string
        }
        Relationships: [
          {
            foreignKeyName: "issues_cache_repo_id_fkey"
            columns: ["repo_id"]
            isOneToOne: false
            referencedRelation: "tracked_repos"
            referencedColumns: ["id"]
          },
        ]
      }
      mentor_messages: {
        Row: {
          content: string | null
          created_at: string | null
          id: string
          metadata: Json | null
          role: Database["public"]["Enums"]["mentor_role"]
          session_id: string | null
        }
        Insert: {
          content?: string | null
          created_at?: string | null
          id?: string
          metadata?: Json | null
          role: Database["public"]["Enums"]["mentor_role"]
          session_id?: string | null
        }
        Update: {
          content?: string | null
          created_at?: string | null
          id?: string
          metadata?: Json | null
          role?: Database["public"]["Enums"]["mentor_role"]
          session_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "mentor_messages_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "mentor_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      mentor_sessions: {
        Row: {
          created_at: string
          id: string
          issue_number: number | null
          repo_id: string | null
          title: string | null
          updated_at: string
          user_id: string | null
        }
        Insert: {
          created_at?: string
          id?: string
          issue_number?: number | null
          repo_id?: string | null
          title?: string | null
          updated_at?: string
          user_id?: string | null
        }
        Update: {
          created_at?: string
          id?: string
          issue_number?: number | null
          repo_id?: string | null
          title?: string | null
          updated_at?: string
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "mentor_sessions_repo_id_fkey"
            columns: ["repo_id"]
            isOneToOne: false
            referencedRelation: "tracked_repos"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          bio: string | null
          created_at: string
          github_id: number | null
          github_username: string | null
          id: string
          updated_at: string
        }
        Insert: {
          avatar_url?: string | null
          bio?: string | null
          created_at?: string
          github_id?: number | null
          github_username?: string | null
          id: string
          updated_at?: string
        }
        Update: {
          avatar_url?: string | null
          bio?: string | null
          created_at?: string
          github_id?: number | null
          github_username?: string | null
          id?: string
          updated_at?: string
        }
        Relationships: []
      }
      pull_request_drafts: {
        Row: {
          body: string | null
          branch_name: string | null
          commit_message: string | null
          created_at: string | null
          id: string
          plan_id: string | null
          title: string | null
        }
        Insert: {
          body?: string | null
          branch_name?: string | null
          commit_message?: string | null
          created_at?: string | null
          id?: string
          plan_id?: string | null
          title?: string | null
        }
        Update: {
          body?: string | null
          branch_name?: string | null
          commit_message?: string | null
          created_at?: string | null
          id?: string
          plan_id?: string | null
          title?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "pull_request_drafts_plan_id_fkey"
            columns: ["plan_id"]
            isOneToOne: false
            referencedRelation: "contribution_plans"
            referencedColumns: ["id"]
          },
        ]
      }
      repo_index_chunks: {
        Row: {
          end_line: number | null
          file_path: string
          id: string
          qdrant_point_id: string
          repo_id: string | null
          start_line: number | null
          token_count: number | null
        }
        Insert: {
          end_line?: number | null
          file_path: string
          id?: string
          qdrant_point_id: string
          repo_id?: string | null
          start_line?: number | null
          token_count?: number | null
        }
        Update: {
          end_line?: number | null
          file_path?: string
          id?: string
          qdrant_point_id?: string
          repo_id?: string | null
          start_line?: number | null
          token_count?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "repo_index_chunks_repo_id_fkey"
            columns: ["repo_id"]
            isOneToOne: false
            referencedRelation: "tracked_repos"
            referencedColumns: ["id"]
          },
        ]
      }
      skills: {
        Row: {
          id: string
          language: string
          level: Database["public"]["Enums"]["skill_level"]
          score: number | null
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          id?: string
          language: string
          level?: Database["public"]["Enums"]["skill_level"]
          score?: number | null
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          id?: string
          language?: string
          level?: Database["public"]["Enums"]["skill_level"]
          score?: number | null
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "skills_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      tracked_repos: {
        Row: {
          created_at: string
          default_branch: string | null
          description: string | null
          id: string
          index_status: Database["public"]["Enums"]["index_status"]
          last_indexed_at: string | null
          name: string
          owner: string
          primary_language: string | null
          stars: number | null
          updated_at: string
          user_id: string | null
        }
        Insert: {
          created_at?: string
          default_branch?: string | null
          description?: string | null
          id?: string
          index_status?: Database["public"]["Enums"]["index_status"]
          last_indexed_at?: string | null
          name: string
          owner: string
          primary_language?: string | null
          stars?: number | null
          updated_at?: string
          user_id?: string | null
        }
        Update: {
          created_at?: string
          default_branch?: string | null
          description?: string | null
          id?: string
          index_status?: Database["public"]["Enums"]["index_status"]
          last_indexed_at?: string | null
          name?: string
          owner?: string
          primary_language?: string | null
          stars?: number | null
          updated_at?: string
          user_id?: string | null
        }
        Relationships: []
      }
      user_github_tokens: {
        Row: {
          access_token_encrypted: string
          created_at: string
          expires_at: string | null
          scope: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          access_token_encrypted: string
          created_at?: string
          expires_at?: string | null
          scope?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          access_token_encrypted?: string
          created_at?: string
          expires_at?: string | null
          scope?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      index_status: "pending" | "indexing" | "ready" | "failed"
      mentor_role: "user" | "assistant" | "system" | "tool"
      plan_status: "draft" | "in_progress" | "completed" | "abandoned"
      skill_level: "beginner" | "intermediate" | "advanced"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      index_status: ["pending", "indexing", "ready", "failed"],
      mentor_role: ["user", "assistant", "system", "tool"],
      plan_status: ["draft", "in_progress", "completed", "abandoned"],
      skill_level: ["beginner", "intermediate", "advanced"],
    },
  },
} as const
