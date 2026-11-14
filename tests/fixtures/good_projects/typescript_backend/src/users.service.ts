export function Injectable(): ClassDecorator {
    return (target) => target;
}

@Injectable()
export class UsersService {
    findAll(): string[] {
        return ['alice', 'bob'];
    }
}

