// NEST-001: Missing @Injectable()
export class UsersService {
    findAll(): string[] {
        return ['alice', 'bob'];
    }
}

