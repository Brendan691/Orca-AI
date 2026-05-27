"""团队与分享 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import require_user
from ..models.team import Team, TeamMember, TeamRole
from ..models.user import User

router = APIRouter(prefix="/api/teams", tags=["团队"])


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")


class TeamResponse(BaseModel):
    id: str
    name: str
    description: str
    member_count: int
    role: str


class MemberAdd(BaseModel):
    email: str
    role: str = "editor"


@router.post("/", response_model=TeamResponse)
async def create_team(req: TeamCreate, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    team = Team(name=req.name, description=req.description)
    db.add(team)
    await db.flush()

    member = TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.OWNER)
    db.add(member)
    await db.commit()
    await db.refresh(team)

    return TeamResponse(id=team.id, name=team.name, description=team.description, member_count=1, role="owner")


@router.get("/", response_model=list[TeamResponse])
async def list_teams(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Team, TeamMember).join(TeamMember, Team.id == TeamMember.team_id).where(TeamMember.user_id == user.id)
    )
    rows = result.all()
    teams = []
    for team, member in rows:
        count_result = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team.id)
        )
        teams.append(TeamResponse(
            id=team.id, name=team.name, description=team.description,
            member_count=len(count_result.scalars().all()), role=member.role.value,
        ))
    return teams


@router.post("/{team_id}/members", response_model=dict)
async def add_member(team_id: str, req: MemberAdd, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    member_check = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user.id)
    )
    my_membership = member_check.scalar_one_or_none()
    if not my_membership or my_membership.role not in (TeamRole.OWNER, TeamRole.ADMIN):
        raise HTTPException(403, "只有团队所有者和管理员可以添加成员")

    target = await db.execute(select(User).where(User.email == req.email))
    target_user = target.scalar_one_or_none()
    if not target_user:
        raise HTTPException(404, "用户不存在")

    role = TeamRole.EDITOR
    if req.role == "admin":
        role = TeamRole.ADMIN
    elif req.role == "viewer":
        role = TeamRole.VIEWER

    existing = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == target_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "该用户已在团队中")

    member = TeamMember(team_id=team_id, user_id=target_user.id, role=role)
    db.add(member)
    await db.commit()
    return {"message": "成员添加成功"}


@router.delete("/{team_id}/members/{member_id}")
async def remove_member(team_id: str, member_id: str, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user.id)
    )
    my_membership = result.scalar_one_or_none()
    if not my_membership or my_membership.role not in (TeamRole.OWNER, TeamRole.ADMIN):
        raise HTTPException(403, "无权限")

    target = await db.execute(
        select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team_id)
    )
    member = target.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "成员不存在")
    if member.role == TeamRole.OWNER:
        raise HTTPException(400, "不能移除团队所有者")

    await db.delete(member)
    await db.commit()
    return {"message": "成员已移除"}
